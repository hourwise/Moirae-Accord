#!/usr/bin/env python3
"""Independent interpreter for the ACCORD-02E4R5R4 executable metacontract.

This implementation consumes the package's registries, bindings, and finite
expression trees. It has no dependency on another evaluator or artifact
builder. All filesystem input is either an explicit command-line entrypoint or
a relative path selected by a verified registry row.

Every pre-execution failure is emitted from the verifier-protocol commitment of the TOTAL pre-execution failure
model (embedded below and verified by RFC8785 SHA-256): the declared family, condition, stage, precedence, code,
failure kind or reason, diagnostic and witness derivations; the candidate copy of the model is only a claim that
PE-22 compares against the same committed digests.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import copy
import hashlib
import json
import math
import os
import re
import sys
import time
import zlib
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

import jsonschema
import rfc8785

_TRACE_START = time.monotonic()
def trace_stage(label: str) -> None:
    if os.environ.get("ACCORD_R4_TRACE") == "1":
        print(f"[independent {time.monotonic() - _TRACE_START:.1f}s] {label}", file=sys.stderr, flush=True)

_JCS_CACHE: OrderedDict[int, tuple[Any, bytes]] = OrderedDict()
_DESCENDANT_LIMIT_BASELINES: dict[str, int] = {"max_json_traversal_depth": 256, "max_json_nodes_visited_per_value": 1_000_000}
_DESCENDANT_LIMITS: tuple[int, int] = (256, 1_000_000)
_DESCENDANT_CACHE: OrderedDict[tuple[int, int, int], tuple[Any, list[dict[str, Any]]]] = OrderedDict()
_SCHEMA_ADMISSION: OrderedDict[int, tuple[Any, Any]] = OrderedDict()


class VerificationError(Exception):
    def __init__(self, code: str, witness: Any, stage: str = "PRE_EXECUTION"):
        super().__init__(code)
        self.code = code
        self.witness = witness
        self.stage = stage


class ExpressionError(Exception):
    def __init__(self, error_class: str, operand: Any = None):
        super().__init__(error_class)
        self.error_class = error_class
        self.operand = operand

class ModelGap(Exception):
    """Implementation-internal condition (model PE-50..PE-53): never a registered normative result."""


class PathIneligible(Exception):
    """A path is not usable as a candidate artifact location; .condition is NOT_CANONICAL, OUTSIDE_ROOT or UNREADABLE."""

    def __init__(self, condition: str):
        super().__init__(condition)
        self.condition = condition


class StrictDecodeError(Exception):
    """Strict JSON decoding failed; .condition is UTF8, SYNTAX, NUMBER_LIMIT or DUPLICATE (declared rank order)."""

    def __init__(self, condition: str):
        super().__init__(condition)
        self.condition = condition


# ---------------------------------------------------------------------------
# Verifier protocol commitment (metacontract:/failure_semantics/pre_execution_failure_model and
# metacontract:/registration). These are verifier protocol constants fixed by this Accord version
# (model.protocol_constants.constant_status: not a candidate trust root, not a registry object, not a
# verification-universe member, never candidate-supplied authority). The stages up to and including the
# claim comparison run before a candidate metacontract can be located or trusted, so this evaluator holds
# the commitment itself: the embedded copies below are zlib-compressed RFC8785 bytes whose RFC8785 SHA-256
# must equal the committed digests; a mutated candidate metacontract can never redefine early-stage
# behavior, it is only a claim that PE-22 compares against the same digests.
#   model        b88f7559e157d318f194d9df3b33c4b4418406e54d358d81aed89fdab2702d9b
#   registration 80f60d23c3354ba5ab8899457ac9bde9bed1913538feb968bcb31a5e47a39694
#   generic_failure_witness (digest only) c743ece2bc832dfe72833a95fe70c81408ad84d874d6b0dc26b14a6afed5fa62
# ---------------------------------------------------------------------------
PROTOCOL_DIGESTS = {
    "pre_execution_failure_model": "b88f7559e157d318f194d9df3b33c4b4418406e54d358d81aed89fdab2702d9b",
    "registration": "80f60d23c3354ba5ab8899457ac9bde9bed1913538feb968bcb31a5e47a39694",
    "generic_failure_witness": "c743ece2bc832dfe72833a95fe70c81408ad84d874d6b0dc26b14a6afed5fa62",
}


def _load_commitment(blob: str, expected: str, label: str) -> Any:
    raw = zlib.decompress(base64.b64decode("".join(blob.split())))
    value = json.loads(raw)
    if hashlib.sha256(rfc8785.dumps(value)).hexdigest() != expected:
        raise ModelGap("PROTOCOL_COMMITMENT_DIGEST_MISMATCH:" + label)
    return value


_MODEL_BLOB = (
    "eNrsvWtzGse2MPxXplSpivQ8YKyLL5FyUoUFstlBQgdQEu88fqcQjCQSBDoM2NFO+b+/69L36bmAEJJz+LB3LKanp3v16nW//L3Vm89uJtPh"
    "7H7r8O+t/mQQhf3erDeaXM+jrcOt22jW60/Gs2mvPzusXPWGo/k0CuPotjeeDftx5Q7+iv6K+vPZcDIOJ9NBNN0qOdOEwziEcf1oEI37MOlV"
    "bxRHiUHjyQw/6JkwGA3jWRxMo2v4bzSNBgG+Gh8FneMP9dNq2Dj7pdps1MJ3rYuzWth696/6cTfojQfB7CYKYL6r0fD6ZsYvBcMxTDGKep+j"
    "oNefTuI4iGe96yguBfEk0KsMhnEwiK6GY/jaZDy6Dy7vYTr48RZmGcEWo950dB/Su+F08iWGpeN/gqvJVMwYzO+C2YQWMhz3R/PBcHwdHLdO"
    "z6vtelhtNsPj6lmtUat24a+L7odWu9H9GB43q43TTvjrh1azLrYSvquftOCVDuz1rNs4Di86dQBGbxB8jqbDq2E0Ld9NJ7NJfzKCPY7h42OA"
    "1rb8LVS/7RwRRPqwouGgN4N/Te7ucaO94G5+CUC+QdCOesNbeHJ710NIw7bP6+XdH4LtOBpF/dlkulPCX/b2aGN6rrh/A0gRfO6N8G84O4QR"
    "/DXvwTvhZXTT+zyEfwAqwEGHBtLNpnNABgYk44+LdZeTySyGf98p/DJG44xyNvju54hn/Ar4NZrE0SD8POn3Luej3nQYxYjivcHtMI4RueC0"
    "B0NAwAh/bl8AwN814ETO3ofV9vuL0/pZN6zV4UDa9U7YaV20j+vhceus021XG2ddfOd62ru97U0JayeAOHA1yoyl0/syA+Sw8h2gUVzpTa/n"
    "t9F4VumNRq2rykvYhPH5rd44kCOCLzew7gD2cz0c4+mYKwtuenhc8WQ+7Ud8stMeoHRwG91eAmhg24mVhnw7qu/hj043bNffNzrderteC9+3"
    "q6en1faCW0l83NkL4lhygYgKdKsIQ4LeNfwazwghjYudfI8u4ZAQ6ivsTkIpHEz69A8608vJfDwI+WVYARMCDYguHCVSJYms4eTyD8BlGKmv"
    "oLhrvtF3vf6fgG8w/Lx6/HP1fR2eDsefAaPgVoUSSvAYCVG7AZdUALn9EUaauAxjTuvdKn6kXT3Gr/BKzEmMV++mw9sh4rT5/LzdOG10G7/U"
    "Q2ukODR7ZOu4XrtoWyOn85E1iLDLeM40pU9XOJyP4ePTGLf+S73dOGkcV7uN1ll4cQbfb3fqiFoXdcS6XjwL+zfD0SCMBkgR4St4MPXq8Yfw"
    "tH76rt7msWHrJOx+qIf/6sA0AubncMHwslW79KjTbMHt2vpyE40JPeLRxECfXoCvBgy3UhD1+jfB5CoYAsnjO8BDYxw7GQONw0UFY6DawTYP"
    "QB4QXHRPyruviSeUYZez4M/oPiCCAlSyN4Z/w6en5rfvh9FoEMNMPCWA6qwVHn9oNGthvQY4IRDfWewlUNFgchdNkVrCOoklwW+A2bQm/Hkc"
    "AZDhX0G106VfYW4EBAPMDx2chz8jJh1EQLnpCuEKeKcloCWAwDg7wocAN7u/i0pJ4OR9EjhS/SxsdMNGJ6yap4fEyzySoDfTp+Y5A3wW/QX0"
    "gmgwsstbhDgDCnASmSSw0N502mPeNPaDrwTzwcd48YCAkh5sHf5uXFMDsZ2L570c3rvl3hDvLc8gJAjM9i9Abhtn5xfmg6wrVUojYrDuk0aT"
    "9nYB0sCpPDMhC9Vax8S5jL2H7dav8O1u/T1JGMzS6KMwSH1WLLtdP261a2IRn4DOgTQ0Az4dXs97cAiziK61CUv5ZeIyAIAayjatX5sN4jUn"
    "gB/ErQP5PHRBBQh1JoU3sV25qqB3BXzBllrKAs+up5P53SE9M0ls8KUXSykk0nwG8Z/ZWEkwWGDEky8oWQYktyH6mfwt+DKc3QBruhK/4r0Z"
    "hPj39ngyLke3d7P74M/heACXCf6HZBLwGYQjLXhOroYj8zvR/8xB8k2uWI8Q0tZbIYXB7NFfwR6ferd13GoyW0fc6348R5SqwVnDqVoUgQiP"
    "lA2DhGyIv3xG2joJLqNAiGxEF0BQFcfN4m4UXM7h5pLIpaRPgVaMtYRaeg1C8OVT87+h0AAlYHi9cxgggbrHU4CrHYPIFuCsgDogo5wBMtT/"
    "+6La7IT8o0Bp+U0Gd4VRIq78nwocEAgSQoDnk6Mzw5MKovH8FumGPD6UQ8YDdXZIRhS+Sw5mw5nJIAtU9SZcm7OLZhM2HgGfDv5OoMNX1h2I"
    "lUlOJQeZnwaKiCpOyWBwghSS9hDrNR8xY/oyBAymj47no9GRoPfhkAcTxcencAOOgnje7wO1vZqPeGbgFBPSRUDxGkc8+wxGXQHbHyJj2q7t"
    "HhAw/ohBBkDEINVwBIejRAP8pfoOuYRAPcF8B5OI56MdAd5U2+0qogZ9mqg60TZQb6pn+OoUWdg0IJ2QiCvQqXpbcxU4MpyX72z0F94X2MDw"
    "tjcS2I4SMTBlhNB/oukkuMI7BSuEAcApYDc0TYfVk72Xey/Lu3ukBV5H06Ng98VLhID47A5ydT5RhCv9hbILSehSJjCWBQMUFzR4IF6XbhvE"
    "dfkzHyaCNAboxVe8QtqkgBv/DipKoIAedBlxkHTNJn8iCjEB6R7Bo/8KeGmEMiPQXeUMpLNJMJa26M0YuaJYqTwStUa1SQ19fUICHiV52J9w"
    "RlDZSXXb4ptLW+TDuO3d4WL5oADzEcEA5/nTpYC+XAr4w6VAfKQU4DdKctElsTOUw4LeZRwp9UZNLxYD8ByhhByyujqMGS+B+4C4yQwFWQsz"
    "yGa90wFxpgqCS5tpSththU1k+AqFe/EcRShHV6FTABINF4wUjeDH/xJD4B+0gCP5tzVsImTR4CcehTOi3gBzIvdfxarsZbB0Jb41A4X9Sg3f"
    "OUpfC4ARsR1sMTHddLJBoKB3BnJfNTxpt/4NRO+8ccbWCbEuYlHfx4rP3U3ItCLpSeVqOvlPNNaafngHjLjyI5/kT4hskqaSgIXf6gCL6Jw0"
    "6jX4RAG6e6hpKYJakFLGGCke8s0r4QCm+UzcSlvNBujAAG1x3VmEng4/E3XDTTAoYUdASBA8yPeV2jGaMBnUZ8zwnIw+RwOavtX6+eI8/He9"
    "3cKTPb1odhvnaNJpg3DTrldr1XdN1BlgTlA//mcekUWndznCOzQDgRnos9TSiDUyh8Dl7+6QNEs6lUWCx71bQBMvIQ62e2jcMu/SEC1qd5Mp"
    "SUlxeRg72gKSoB2h5YCoB8YDtIw48qL4sgKHgJvUG2HlsAKA0WQ+i4G1ak79458/8dyn1S4oUTCzQDMhAcKu2lKqwXVPP6N0Mr6bzxDlhmOm"
    "iDHtGcl/0tr1QiAgi3MxMH9UeOmbsIn/vjAFUcAFidbSzMXHAB99ieu/nYB4OLsBgrQLwIlu2VyIuqAygOHPGhDquPYRhii78FEhAiCq8xIc"
    "BDCOG7kaCWDS9iVQD3aPSF8ZDioS4bdrb3fUHWaxZStBOaX2ioisZRIH64UOiV/usWQRIE1AfZkmV2ZfJeTOwB4TzUwLzhV+SFoDQXG7RVxi"
    "IYUmZOHkZoi2WOB+vRFqgPDeFJjbcKrwFwS74Mt0AreAFVbYEN9fNc7QFccAQlg2XT49QIuC8/EIBCDeFYsQvK1Yac2GJWYC9hG60tpySKbx"
    "k8ZvQJDaLby2v2vlSnFVrzaH/FIN/RlsePguK0y2dmpopsoYTMjahguCCikpjx3WNFtn8J1m499SiTtvNRvHOLz+CxLMY9QOtQ4sbtQvsExA"
    "Plhgtdl6zwuzFFOkuGG1BpwHlbh3H8Pz+sEurrf+G5DKM6CV1ePj+jloH8doIpBqqHrabV90cP3iIhNVN/cifv/l5e5++L71C77ES02FHPMA"
    "0AQE6ATkmLXXa4emFuUYKZW6Bh4KtB/MQLSqkBJgqG+MQsAa+/MpmWS0JoZD40AAESQWLwzh0pHJCCZR+kK1c1yXRmQQdgC2tfpv+MAwZML9"
    "jPvRmIRwlFnLlz1Ue4TNA5U+gAquAEaas8D3wEQUatNFtQMnSGBTWBGetzqwxlq9zR9l/A4vUVwj38VhJUkrK2i+wxtE1lcSEACE0x6SmB6K"
    "wdbilbGRLGlCXSZAHAXaejyCiz4CtYIJPrkegCiBfjclWoOcIfF+sA1LGtB3QDe9QqILavgYLu+OMPXha0ADpaWMZgAaPBmDXgIC/ySe8UST"
    "z8JuoOxibIRC6ySTL/5behQEtIW9v4agBmA2gcXy5QCTGMCc7lbiLOnYxGevfJwIljZC7QzZl+kJsw8Z/RrSgp1+UmlzwYLl4sNfG90zlCtb"
    "5yDigAAMi0/DiBz33nU0BvTuh/KJOI2KMMnFqahhHWvJOHf7d7maspgY2Mc0npUnfb6RffLfZZxRrU7XDewMHfMKpO5XWdSVcwOBLH4DqcSY"
    "76fKIJoh/xrDOACBXIW130F0N7sp06LVSo/ERQZBghwUiKL6vtP1PpLG0kIW6eTWgdZWkUpWmwiEerPxvvGu0UQ5GbZeQ1KKkqaCgLFgwKLZ"
    "HKQXuo22So/2cRMbInCbDi+HqOpVtDNEinYVsfSb4Z12pO0shdLGh0IxK+C3ADjs732z9Q5OlUUmQuxOvQmUGJlfDkaLU6b9Va5Hk8veKGRx"
    "i9CYhT12VlpgwlNHE0McIUEy8ZFtcn8ICJI1GzzBwF0QAYZSblQn7UdbwVe0eiPEef+Z5RMY4aEKlfVKgHGp40idzFg4HMBJWGu8rwM7WtHa"
    "UV0NB0Mgz+DcoyOlU3thYIQ6aedaLLG5lK9V0r/2VclrLKicNNqw+ZNqo4mcmHZPFp8FEJLohqKtUpRwcVHTDlQMCKsE9inehsKHJKn0JIbh"
    "Wif3I6GSS5v1X+pNcAa3QGHtop6NZtlU6eGqdztEfK9gFMBuRTHskAzyCY6gnMgsD9AgtFBpRg+M5E+xbLLEX94HJpSCVCh59/TfFw0kkEI+"
    "FcjZWRo7pTYRCjPHg25W6mRfDUfMSQOF6UL8WtLiUP5U8XpvAc/AGupnYILrjEBf7U8gCODuZthPaJgKA/1Ahzl2X4ORoEaOm274c/1jCrwt"
    "rke6e2ywRjj4BBOMI6TVfeE4VCwRT8vg1STQtU+O3755+8rgQXohGDogLoOKHBAi++9bOtpDO8+0N6tBDhdSVFq/kg1EqXxsKKuCBH6CjjDj"
    "dYl+uMZ24xyVhtPquYorQeXGFrfDq/m4rwzrx6Tygb9HsDkK/wAaewyKT5eM0wRAAAJakj9jJM9IcLLgEikEiBRsMWdLpOFwRVRBlxixLhSh"
    "D9H5Su+whxa0YhG3gyoJO3OlftSH2cDYSZI4z0xuXlyHIWi7a6Epx2weIK8aTYlTYWAU2L1iNlqThSaknygQBg91FF3N+KUhGf6N0X8NiXTz"
    "4CNQ8vWKwEgSRXfJpUvjN5C8s/fdDxYklbgm3cxSlP0+1jZYgbnCeNIzjWnCX0EkxQwhMKMSpHFUzSejyhQ13GIV7wwvU/K0tdpD+g2b3/FH"
    "trM5C4c7Q/Ir+gwQltrYwnMQSNBDJM2cd7370aQ3kB4k8ZyNgDVE5nOCGZGJgERfOnoduMDuWFqMCk5A+49a4t1oHpMOZhwzRswRRmkNDUxU"
    "wtUPnwA73i0DG6cgJ4ogtX9bOhq5U/izFB1H77G6xJZDgMd0jjFH0+HdCGxK0nItjFU0BkTj6C+ABrqPeuA3uwPK3VfO3B3L02960n3f7hnW"
    "QUl0IC6PJZCSsveVLG+w+n2IMYls8FBvx4blmj4pT+5q+JeBTYbhCizFcHTkN641iJRA+GEV/PfCxwZuE6DCaLdX91fAntiYwabJSQes/x5D"
    "Ael6h4KilqScEYIJ9G4E2y3RzUezSGJIDEGH8BxA3v8TuJrggCWDauh3Jl/GOIc0ugtxjSyMOz6neBbzJQlDR0yCx4j9o7asIXZG/oKe8piH"
    "RqSNC178cK0KIRMY2XnRdbEBPVNz/IzARokPHDypcZPEHhGH2ccA0vGgNx0Ik75wxquAgW1gda9/eLlbkjwPEOVDtbz36nUpuAY6eQmKTinw"
    "+D1LZPKCGZDPvqURO7hV+rZCgGq/D0yWdz+d9+XpKy1P8gc2PmsuXHKM5+R40VAXWqaUSshmLcxDIWmixPp07EjrV5QYxpG6kKG+kFKCOqzw"
    "b5GM/gutsA6Dmoq5JKUShEvZJUy7q3Jz4Qs+cw56vgyfo/AtCDZF+uHLFy/20Ysq4kk7cGXFfFY0p7glIK7PIna6dlG/OLe9K4JikB9lrP4s"
    "K/v2IOElcMKHHDjCFRb3YBBI8FUE82TrzLYFxR01nbB/qllxdXIGmJOOXhp4roIMzccM2Ayl6T40MW5LGeCkqVm4HenSlOP53d0IN5BBrRNT"
    "hCpgnNmFbz6XKQglGCja/UxYDkGagq3CWHHp9HfIBA7/j66+vPWavGhLGnHIEXom18lXAF0fZCGBVW2zaBgov8AOKYWEzFLgIOHXmHCJychQ"
    "rtwU5Is7b2EosfQq8N4AEECthjODrklcpRtBhNyeQLk8nBmEZqB8YNb7lmsw/V6mOPy0udxm2GIWISslhCcVI2vOAP/6lxDJJZFYgEAcsBaj"
    "qCSNE5ysdnEMCCTPyvLMiLXablBBrpF6SG0S7xrqNQyAF/DzYN4nlouojM4Qk2l2pAWNJk+kEhgc0gpWi5XBTNkPlN6Tc6YUug5qCaKeUOdj"
    "5RlmWVb7h4c/SdKjv3Nx3mTbpmH/Y8/9HD/J+DecCgAz41zaHmiGTwogydXJa2Lt1sAX9aoMyrTwLmNFTP3mU+R1d7wl+tk8wEQ4adOGhTs9"
    "I00opAxDOdPHkZxV7zl7OuaxvkhU/+ugUAxvkeKLYATeH7tbeZcyjJtCDnFnbMyRt05dRckbtcPBOHTx5A+xU3nhWFzDkETjREzmbFgCiSdL"
    "MZUFJMeUhaZ0kNXIigC+SiL9nN7T6KjT0ERAIoyOTRXyH7MArRmjabKsGLRMPiALEZIdOO9GRx/3IgjPwp827ALmE3b1xqGJ+f6YYOcOYAQH"
    "QIQkRUk7VRKRiv+gkzWn5MBisXQ13isgqpdddxboLqdoJLMOzfAhqUwaqf6ipMk4xsGMv6vYo32KQwpxbexKp8h28oR3Wz/X1S8yKFv/QYEc"
    "HBoHHLt+eg5yow6os3+xx57V30uXvoy2Ew/BddtwnghJPyTu6fvFmFt8TBok5QYYMyGsCjIVzkD10wPsEGL3BzXzp69kNIRwG0xFuR1Op5Mp"
    "RhSKmFA4Bh2mUIOw3bMO/uu00W632pQMKG0bh1sUd4nRYKReVlS4MWIxhzyV5ZXjIGITf9F2OcEDpSxCYUxUjjwpsVGCFYYIKfc9hq6dYUiD"
    "FK8xhFAnHk3vddgzineGb0MOlFKNGrfNMe27+xjy18OFcugz8ivWkuGWYQoO2MjfYnDJF/CjhvxE/LwLWLkEBNWawRaq4FdRDFAHQFeEOFBW"
    "i5bAjR1AmjB+QbsRJAIIVMhvQLipXhcFsB1/wAi2I5nruLtf3n0l8ydlRLf4ngcmPyRg8rsASon+uy/+e4DItzyUeiLU4AscEu6Cg9wxxCc2"
    "mGpFYWUxDBNm/JgnKgXqdY5G1xOTacsVsilSWdh1yN+hcMmDPPt7ZdPpVKZb3FkpQpn8QrrHKmrLaK1k/YxiE/lSKgqtY8ccyHH+AoRfRxjr"
    "zNkVFBvHNmWxY7BHaDk/FhZl9RiMGVqvNXzExgRvkhA72POj1u5bRqndH/i/+/vyv++WxDFp+h1DMgUIF/daCo0r0hitvUUmdPj0y4iXMgCA"
    "hdAGhhYaCMFmW/6OtBWQr08OOYDgJQOftBws54WkW7zRgSVivVAatxOGYK0CgfnSg5MH+8Uu78HLJQGLcbRCFjCEOLH/CsSAk421InKUYdPE"
    "OlTSuANshhTkK0vBKw60EoYik4CrDGnE+dl2JyKQULPW8Sv8mSj2wCWFqB28EfB4uyQ8pEmCU4IrwNoqyj4DQSpxHwRIVCcVfYeV30/GAzsZ"
    "26b4VrAl308jaUpesLdHxEhLRmAcgsn4Jr6oksVJmSjrPEB5zZOw2n1VFjaZshki6Lu3r8S91fd3OSiqA0fzpKnRGrsZDK+uEBzC5aCTuPQY"
    "cqAKl6wmf5yFDK6pEVQMUAI2V1RgqwD+m3Y/n44PbyfDaS867JGhtfxyb/pqun/4GQIjy9fo2OFjUm5MIzZUeGThx5cv9sirCcnsZGyVVnN4"
    "xOFIOiab7fmmu9SImBNBS1KGJ5UA/7gEY5Kx7fh7NaF0LYo8W4YZQvUL+I5vZOQzzjIWGSCo4HPtAZkkIL4mSJuMTHffIf4JQcKYrw83lEcf"
    "Bf9v6/9t6fhl7W1Sa4Edq1xXXBjEWFMAdwx2O9Qz3DBtzh91SQakCQnMjhPQsFFdEApJaTyk4U1Ze4Ilxqvw3WxuBa5iodiERhq54Vi2p/v6"
    "CRFU4qUTwwzvQgaR4Tir/3bOKjaYMtGS6Trs/RZMYf5kf4xMbiIQgmcZd5Bldv2k/Xe/2/67T7aWZmpeOhxTzlUrtFbHiruGRUrnIMcGCHXX"
    "u1JpMmVmIz3tJDhJ/CQ/FIXNE7pzSL+1CddpkWms/CSSBFR8J85gZ5JYG0862NLcnyl+sHRgKeXSAhpbfFrtHIhZ5FuBr5LhJ9IRMjqSMWGl"
    "rRwYT6XNyHsEMq9Dn8MKoe6HcEFQ6pARZclQwASOBXSK0rxoDcZgyvQis8CnkgfyVEnFyEzkdERt0NL4q23b2tCoMsPGBoqDbjC8Imcmw8AE"
    "7w7EgeMnQYP/UCu/PFgE1I+NvYZtiOCNw4F+ilhI0s+82IumMuEKtuo2KBHl+9hycNu33PKKWrsstHLXQmWu/D1EbL2DCNvEqqUnmfLrVJEJ"
    "MNsM2BdmrdB20ZQedcUpvEp444JtysGkDJ+b6K8dufZp74tn3YWZwPKrpsoNlL5OuW4yrCflUlLGoEqKM95GrR8S6j+mPPTdWxKCRKpzoKOI"
    "Ej5zYSmK2R6hApjJu6sEf+GqBwkRxUWUTd4E0uME74XqNevuvt4pisgWl80KWykVPouEpfUrgjD/DIwxlMG5Zb0W4iksAm9KGJRoWDGyZzj8"
    "lKVpZYA3QspwvjIlfUtDpB4lI38W5ESLI7QXiMy9kiwmyTWs+lsvUlgIegO1hJ/CEmq7L3cy7u4Su/MQdE4H1mobh/5sHSIHd05cVAgwkJvR"
    "IsnsrVxja5kylisBd8HPZSUeBrgXzBY3EQDk0ESML8AKH0mpsSiOrEjYo7JkwhXaqKLMkbUhltmBHX6na8pBibhcUTiHlC8ogxUS+U3RSykm"
    "xfY2HHwT+zJKruGGrCo9KprZc1/skmweWmmEC4uyNOYbhyI4nGwGw7F2h0oJRHAel4CkhDNxJjX8Uha/cGjrlAqEwBQfdgO3OJwjg+4x6ZE1"
    "ptKqM+lTs+KvcuTSImKEUzTJC/NEgTufLC/B7Q4Otj/s7phwlzBV8UJaAVO56PIYFGQsIGUUxdKA8sUppYdDPRySRjCSicBuGqMb02M4Kn4X"
    "otCnF+pqmNv+2x8wpROy/eFQ6p9fLegkp/JP8HDAiOwGNwhxISgZpTo5TOB3juEVGKMhpuKgzWQQioGAgKAAnWeiWqn1vqwvYSpNVpCwjX9u"
    "voYGa1oYSFq0mBFHmhGP4AR85mqj6TJugeOyktHkklLPKiMqxLUuVvQZ+YqIYVQYPnUIolHLQIPZiqHKieTKDpvyBMeWil8OX7Dawy+MEzOF"
    "sRW5cLfCpzQhQew/Wojn9WZOQKB7HClFBy0hMCvocAmblA9GVmiYBFGCc/mrjmaxL+8bbgqzzEJgz1ms4U+QdjA4uxyjhlviUUq81EMRDKDH"
    "IpHpTrJqKxql9zyyJlc6cer6eWvUXTmqPqjz38dU+9AnA6VJOL5SkQtViiwsqDqBS19N4mBWJDRL9AHSsXr/d0Y1Htby8Dkgeaej0QEHKU8j"
    "Xi8YgjVJQit4DH9FznIhSmcdZ4z+6tEmWQVYQUUgFt/Qn/R9LAsZUbiBwgOlMOyYFQXZ/811jxgJvMWGbCxwyPKnRBHFQjUUfYpM6kEtaefN"
    "xiNTmTOYiLSy5ZSAdC4g3bPDoKggqQsohZ4Lyokl+hD+K9A5+iqjXZ2QYIWU2COKGsEw8S81SjLEHde2q9cnGU5J2PwKHKMqr7acBLsqxMkq"
    "LffouGMXMnPrtObL0HYag8YRLmnkdWXa1vc0WpxbRHYxhpWkwmmFOtA/oiS+VFBksCaLEFqeJvTxptTo2F4u9B8IorJNOKUIXiRee2FzaET/"
    "Hb8E7BN50w6qQK1dUXkKBmdVR1mZLS951gsYSkXBVCyhyAXhjCh9s/Y/2cZ2FBOUKp+ErYjVeGSLq6UzLnRvc3Vf79VN5OM80u1dRNtMnrYN"
    "lUQZ5gR4XLEhkftg3Wjx1Fb1t61i0uY1dG6YL/nEm9CSlTuTm4PlyZwqrceMUComaRciGhpDsvxrq+KKqWYK3lAq9ixirHAJsEfWFgmZLD7I"
    "2qtagiCKA+Fb8gkamYqIOj0RYyRcc9JcmiY3u3KRZRt5CtnnoXKO2sCDJGQ5CzL+Qy2vKhlA/ebKBEpedRPwFpJWIQR9I7Em6Dl2acHKVob1"
    "tCCFl7dA6aYWoUcXw8OM/6sgfQ8kZR+NJTknLQoLJ2mMZX9QxaBVJAcX3GLRSc5B7Q5UnWi/wcEYa1aV5onsSBL9ia8es1rKafrsECrOw5+s"
    "+sJIf+G+B0YpeF3aWle0pg4HMy5HzRWwRaVgDP6liv5YVAAziiDawZwgNmr/itLZcr2IaqJQtofgeszLK7zJxSp/r+FOW6KOrZT6DWQ2Vlja"
    "ppEeXyTrXsS02GXOzP4nrLOhmTtUtWO4oLcVFyJjjrZVtLcYhWkHErF+91aaLwWy1PynnaPAsq5BQ4wbsU6PTpFvFl8VpuRVP18HjrSauDVH"
    "2zELvjdbwgSajiocpa9i6ntU8f0yAmuynS2ckybMtWLMN6h1i0uaCnN3cerCXFC0JP1Sdv4VYkRGrf1ScSlhCaXeivnQwQEyTlc3hjDaVorK"
    "d0W040S0tTZsJT/Grl9VM2sYp5fhka/Ev6NP55MTgJBaoG/5CPoHOg0XCTAz2wuoeGmj0USwLYVfIINZphVZRPtxjScW3qh0pL/dU5BZ2brD"
    "k0xuz4z6L8uAAd1748oTT47tIcRAlQp9GHxf+T74v0WQ6Eee7SBIIuVPn1StWhmnWEn2XaTQBdtvtu84GrVSsYqgdvcs3IoBX0uJe5sG72Wv"
    "rWTh06s+fhp3D2/FVAWLMrp2Hn4tHw4FLth7caZs0tBV912jBuRPljB24ZIVFww3OxEDbMT2Vn784yeQYNGlqm+kTI74ntoEXw4HwDZc4AH+"
    "jKiPLQhEIUYOl0gQJt2K8vrmY2X5ppYjf0C1Lru6+A4m0nEynlOjUibabct/cI8PDIbDQqzy+RLHlY2/0lbtb47wqEkbHkRYlgSbXW4kCS6J"
    "/EKheTjtYGQXGFJbRMlT6idzDSoLdzbEljI7ySjuYsQ5o5vNQkZvdSVE/89V3gN2xlgK5eg+sHA486bIkaIpS9510aBcIf6uFz9lFpxZADjv"
    "SArlcvmqrysGplPtVe7bi2RRTk3jjUPeSUvt8mRxrelUFgGzab4vJIrYCYiuPKJS4MxqUtyO7fCRkhQ9SO+0u10LTAGoMjlY94c0wuETYV8i"
    "RN1jkJLpLaLLkx648D5SaV9SNtfhSLnpfMnurmh0KpTZF2xDKloY3/QwWY1sW0zexU+WtcKX8eumUC2fALCITzAtdfdbSyOvtasn3RDr4Ya7"
    "ezIdpYgkPJiCJ1K9OBj2RjLeeOHlLqU4UlfL4yqYAxjI4Yf6byjCAjP23q3/7/eX5R965atPf78++PpdgTuWfGHxnS1w2Z5bphW0t0xNhbWs"
    "c4dWZRCdfp7d8LIC6bQhptMeBdYNPgzSyYl+JZMi5ObePoRC5OOqnzJIXMmrg5CAo5YjnM6iK7LaPGB/Yl8yCiClVsGiUhaHa8pQe5R4gURy"
    "X045BEKSsAkVdIjQpWm0NAIV1e93lk8EXRQCqseKCcmO93C5SxmldmCHBaoKV7w/muVL4OIqQ5maRIXo+Td0IPEYLoyLvRhED1jsvGW0eNmu"
    "/bBTmK6VPPmlUo9Naw2Xrylk8CmrfKMF5+eSQp6e9K375HAxIlZ1t3d3ls0GLy6YJIpmmqBbW7b3wqqVijfMAN3j3ehsoBXJ7k7L5CYblYwC"
    "WKChkirXnZXfLe9fTpunvGu4bHK4TzF/eIWVh2jldADbGTVa6JOPVU+lAMg4qcZDY2sF+SbhiIgpeFgZp+VScIa0lr7l0NB0Sys+0ll8YpkT"
    "pPc02XnsEiowzl1TgqyUk97VgtyiUnUyKrsbUVGiKrwlSpZEjBu6YQUPFXZ8kDf0SBE47ZYRN0YYPvykzArGO6pdJuQ3nm3PzaSGiKvX2Ctx"
    "3Me610XNFun51Gnmt+IsxGMckhGYhQ7TqWonK0qKlk9sGhNRrWSQV322Ie5lGyzJcGCY0gZz9uajWSjzL2PVCxuLO2LZTzU2FN944Y4VWbOi"
    "yxfV1IBMIRU+YbSr0npEgXzZ9LzWVRs/7UwuE+QF8re2pDN/q1AWl3b9oyxD6PpTxW6KmpHV5X2b+6smsrtU54DVZHiZOVveZUit02bLEp2G"
    "Y6uerm7sI8Rk2STWBsVOibFX9DATdY0rRmVjlRyWnRXsSxmTnD2rl+1qwmE8OKfa6nZSrO1OBqoy6zmNsORdVwnU/rIIvn6DGQkBeYnR/nBV"
    "T2DlkgK2D2Bi4TBty2998tmbuOm6mM4tBfogmAkRPd/a49mLAT5J5VIJvXv+TpczOH8KKTJD14x0Ou/OnkG1iAehAnvVG2cc3qSixdKacRvA"
    "lJJVwoHCxMpsXya6xRDlyq5jW/JZ31XaSSi/eZQoK4tkzahQPpzFJhNlGnskZ8KOhfQ6dUYTLS65aeIcpHAnr9zXSnTZEGgnGaRA2ooTxmbQ"
    "2pzm6QvHk6ViB0yNiNE0Qn4K4IdDIBgrvsN6/d8N7sGmNOy3oyuTp+Vhhsm9emZVezz3kSJMV9Pe9aIEKIXcrh3SF2dqeigITPhzQcr8svDm"
    "KnbFwSsaEuIABDOUWwBHyfA/0ULATFKx9cIyrT17Kl/g8DKvoKV+LAsiFizfzl2jsDRwMioTqWQvDukKzGgtretVgRi0bLhn96xfd4yErxF9"
    "IV2tIhoCh9qLrpvSePv6csVfCvPB8veKFxgieMac+aK4gQ+lHIRI6Vr/IrVrvYMwuAvRESKWLA41jeHY2s92j8OsRRZ0In5sJ3PHq0I082if"
    "FtcSLHY1Rh6nGhD2vKv4e/lVPL38nByJ72NKhOG+HlboyXbt9QKxISsuCeQBp9JmVilupzYd1I2XDf1Y2sA8sWl2jpMNYEmP0TS/V0TTXbU8"
    "Xlqt3qtOoln/Bb7oF+W9p8JELKU/kmR0uop9AemhdzsBeOseE0S4MM0Hqa7VFlIll2wvI8MLAxl3QjCrlKONDVND9KpZoMf9XE6HPCsih8Q+"
    "i7++WagcmlmEbI1yTWr6e/ErmIwIPJTeaHGkkqqV2RtrQFhm3ujiVPphmdYObbIpQuoywgNTfWW2f4TOG707UbdL3V6xw7J4qFRuPCQciNf0"
    "TVHSl14aoPDdfMA9tL6dJ236GIc28ZpQkMqOT2gxrnFSY060Z4cbjD3Dd18HmHVdBlo5ww50gaNaecQMa+pDP9eTMhJJr4vwRSVccQ6af5Qq"
    "K73AzIYoKEhIpjQIVAVX4BykKSRoM3WAxzW08iCN2jXLo6yjc8Jx7b4GTK1hwz4IbPq5/tEjPy3uPFlejkJDuuxaCSHq581qt55LcFR6KCg1"
    "1MmMimGZvHwbAP8jAzLUgBRPVRqo+HsH7weE0sywE8OKK1iuzqjWOW5hal5BhqzEzDwz9GGQBt0YYogi9EWBI0B2ORdUlYtSGlDbSUTrpxrs"
    "FhMB8GTF0o1oMOwjxqtbit0vYnhwD9tfWSY9DXRVrPyBvktRleaXRquZo6Aoyyt5F10+cBhgpRqsNudYhkR0B9SyASo4wG7eRH3Vi46XE84t"
    "6sWADrdkszCMS/gynLiBDJN4xoorR3SJF2XPFE68QRtsCfMdqYns6LCS1JgrPdCQURsi7/loCJmRWOmQOSvsyL0HEhAOmTF3K+7GEfSHRb8/"
    "EGMPZGhbEOI/7YGHjfZLraPt/CzoejkSDDjZJeco0JW80j6Q5BrJjyyC9w8oY7RQctfCyL5ifSe9kXQORVWWPN1uXCo9JftoEr2ng7/hp692"
    "eIbOyKW+tHhm1GCuJ1qgWu2IUcYAXO9hiTtsjqdLHX1wdVB9Wl5elrp9i3QJV6g7eIWKCHYthCppPEintlB/AYhvh6ozdelwJ9KbjC39+xz8"
    "+oeBbLgIGb9QEgquO0RPlAIsXGM8w/srnn2lEiNwENPJ/Nrs56dHs+vbKUphX5bMrvRZocZLdM0w2/xllGF3elRqLASeyXbhQ4F+aohZjIN4"
    "dlkXZ0trjynje3ZWApACOQLG9hVmLAIHeawvkgApYb6rB7xPsTcVRSbc1p0ie1NBYCKNI36UhaeioxLkMdIPCs93QnHPE2t3Hf6X8+FIxLEb"
    "2/HcOJOuUWyf8flTiB5RmLDG6+nhKriU9PwGK68BY7EcIV30iYYHVjOJpbazsmY9zyw3xwSCYHD++FERNKsb1qk0Y6ORtBr3JID2xZiKCnfY"
    "Tj5Z4x2rfmXUd8fIsFVVcF+SmMnHZq9ZUVxGbcAOtPHuacla2VtP0S7Fu2WlPsodp1RNlbXcvDX1NqVSV1oq9bG9KsshBv9QRzmbivoVK7e4"
    "rhqLD237sTQM7PjjVZRczqIVvsrLj9WvZxGQOLVyJfVoNesPKpRrMpn/JT16vFA/afyGjAnBmXS9KPXXm/dUsJkPrWa9nXZS8MvaGyXmVGun"
    "jS6KOe8gvrp+sJvs0SN3ngjp9fbHyezR430Dyh9YfYuoQw2SNm9Hn52naL2TizcANOk2MtOCjo/r510nYTOvcAt82puOmSyqk9a1V5TY+cmJ"
    "Y5DdohLxDCtq6etqZ0/V5ze13pnUGldT7cw5b1kHpwAoHrG+oG/vBu4tUD9olTnDGWnCyfAB8MqmIfZOyQktEA+ok5FhOV8ldj5RLHy+B82w"
    "QCMeFnCo5cMhPcF2bQHLKZm8WaUiQq9PZOFU42TsZTKIgZ1Qbj40+FMjDqyI4Wjiq3tyParM24fAfR2Jzb6z4Aoi8manUcxkiRPNgyQvsWEN"
    "6XSCDKAp9vVBPmwSrYweSA8XK/Yn7ay+Un+P3+ubj3yJnCrnRihrsTeVqhhGLpFLBXvQ4ak5edKYUyk0CJlLZpj0XO6UTLPmwtUJ9sM2MbEK"
    "uWfDHqh6GfNEJBzxJXfLTJN/xGtV82RfgxMQvbCiK+dVoOJwodQ4+IzjK0CTe86rTlS+l5m7uEokPmbdXpHTC0FBr0rBww15peX7eFbPQRss"
    "fH5Fj2OBU0gxehidoygoGq0f2MCLkIhqz1JgFvDGsv5YXBLlUftA/++N1/12k9VbSBJ1yDDGS9jjli1FdmT48szeND0B5TKZkCSZpoAN9k2I"
    "V7aNlOAXwvqIctrlPZlOXgjwTeBopuCDjoNidiavzXGlXbwL4GFR03ISU7eethm3bMH92LcPg7xUOJdlQ0u/aUWNzhvr8sqsywnEWA73c82m"
    "OfdgnZZTX/7NatDfJwtY90AnfvhjhF/4snK2Ne8BicBdOnaAYdGFqj2gDnGFKsrOE3Tm9hmbdYbTg2zNJjxIhBLsyJ8wYh7OzgNs08+wQ7yH"
    "+flQFWH0ncZMK/5mCuXAhreRzaxJ0vwCGCQg+3Ar6dJ4BP+6OO5eoM5DbEoYPQpc0AyM8veWqqg6UIdOgxAZE2f2KNIBqCgB5ner2uaAgc/R"
    "uMxZKMYzEsxl4FDMDf+4s7p4Oo1EbiSTDxTrVayfscydxftSPbSAlTCqWU3kpaFatBtCL32hnn3+sk+aTj6oX4+nR2LCUPcETRIL96G36iKT"
    "BTqrE3RuPyWuoWU10tKxQ3FeudlSfquu31WDLKe1tJkllAzvSfblWNWhMNAaosyShB4W5l3KOL7p0P2grs3YKI1ToWQj5nWZwmCdQKw5gB+i"
    "dqmFkLiGYiv7yYhgo2VoSZQU/2oWy8UKswFNC/+PheesPQAP63TJalptNzou4c0kAnpNuh660aQxa6HZCwy2dQwQR96+dOqBPmjVaoWeghf7"
    "KBB+IDkB7cjYv53y8H27OQx0uQqja6v80TmTQ1noeKBKhWBRg7I4saPAa/xh6ACDIaEaip7XG+/P1GptUToXQsItEFOlYZkDgpcP3FYvK4ky"
    "F8Kds7pe6hbC6M9lYUwxGAP0OI2AsqbHZbYNs9QCyfNRvwfFicg79zJI22Ygyi/HNG7XW0TkSYCbjcC8FGrX0DFqA55Wm1ghnzQnHdvhd8Gt"
    "rF41vMmFqbHZp9GWx1A70MpQ/w1oIFgZQl4796j2+KAg/8M8SOr5xvZnefyigQKEgE9kfcFZ8PogwBy9KdrQgxtoClW4Gra5nkcvem0cXHgG"
    "JgFZ/hqZABg2r8eQEAatMcxIjN8T8qv0W2GOwOsDA6nSBrJzHKs7o6iBLYzSx4LFB8ggd21NjpItA8LTRoc85J4x7eqvsmdDxijVxNgzVGZv"
    "IYQ6stol2rDALsAuZrCvdBDJoZADVtbg/uoAh3YDpQhIWfMP19YxusZdtt8mRkuzDbqmsHs7BMFUMaUZcaULQQFgOrDeaNSsVYrYI4QkXD02"
    "r2F6K4Q8gnu52erUa4atzQUM2sbhAlVNiMixlIdnlBXDxIQqcC7PUAoyrDVOTtCdCuLYqXHQaDVoELLK0aQSwB04liKY+oYxSHlr1QHBdzsc"
    "QSTHdOFZnfHMpEFG/JQzUmiBwumsDUapI/XuPbuWQzmdyqmHCtDCeCbEBGm895hRaO3Wc0QuUpxUKiSkgWho0CNAAcdg6tmZjABNGakyWBPF"
    "+LUthVanqkzTrdcklzUK69C199NLmUUFBnWM3kGEYvhdFRqRObIF7RGA47FjN2Wg0RraHEExB9raJUCHZCA5TMadQOL/2+RTUQcOsYlA3GxA"
    "IGByWOcjtJ/9zSCh+rnfF6ENPCYOJd5CaNEHlGkuMSQHquaoVIjaZnE/pqWNFlc0Lcwx7TUbSZ0xKceaIQclB3lAZ7dOsz+SfKboh6I+kl6B"
    "z+Os+XGrZMT7IDmkrkJIUH6hcveQ2lUXJmmaRZTkwsoSUuJC98pHQEtgX+Crh0+iYIYEQOOuMnM5zaZdKy0cr3VhTTu113hbFazpV7MUNAwk"
    "ukQ+HUwYE86dDj0RkhdzGtqppCvu/c8a6zZM0IeY9ZYHbbKG2+JH9kgDDdRA57PvPnZJgigwVPTGIqha3urMdwg38BVfv6qMN72UPHVw2ik5"
    "42hGIopFN+CX1VJHK9bLO8YguZN29b3ISkx7zT5TJ/gqIcQ6z30SpzPEnv891BIAQYbELZT0pK/HdJZCV9yL8/NWu0s3XHIS64JRpxAy/J2y"
    "21SLl1qKFGJHh6UCa5AlK+ge0OIK6XEsODTrv1HIIVVCQUkTDqUGVxyzZTvHVfgNlsQlyIlmUJSqVPZS1u1UuAE2p+ngOcsWYhv1347roN3U"
    "5DAp2OaOY59yzjBNIWFJ50DvnOdy72b3ELhVLO/qkYz9BTfrG2w4+/QI1xlukGk3j81hTGwzklICqXHJdzzUT34JYHLRZHG7E0rkV/SbrMCo"
    "KWiS3qyevb9gl57EJ3kDcGnCvhQ6FXGN0YnEPJ8knVdpVF9UmRIt7Z4yQE49J1SoH1/Qe/I6smvcvoDnbZTOELetWyOiHEiZgv0cXzQvOvZo"
    "MIuBoN8WKQUAx9RXdCKt/kZabLrqe2P2RdKac/Y7OC7ZNK1kFatQB68UpC3HQZ1OrGz8V8Vp9QGmXJBiqJJ/u5AyndcNNEh7RYhNiYV91Gyh"
    "+gsghfqycPormto4PQWbovPUidm11uEMEZJ//gh0uRAP0UfhHwi7POvgSfgmTdZAKzTIEuKccWQhAgDBhbHgmByEOJ0+BBxY71P3KA1caZEb"
    "+WNN6ibf0sQGiT/A0AMSHIh3Krzo1AUL9asjZogSadsqTsk1aWhKylq5YrPahkGf7aSE6mWIUK4CmCUvJqMBzNNxnxb/Zo4A5g4XFmPPt6m3"
    "3oUQXQVW2AzSU4TAIHcpNgaT/FaFdqMASydItmAdQ7ElbdmCKEK4F/XXZep8cfbzGfxis3HbqJM2ii1A9FShZLo0YAyydela/aRx1lAf8gBF"
    "AK8jd6CBtIXtwIgnKMonXL7qEvixPeXOgC2ZGkEOKUgcnJrYroaiIERDGnixevxBUEysW4ldFqUGwQjGZielWSuXhZjR8GBYVYbNUqaeTh93"
    "PXDDiOKbsuGxOTsG1B1uJcxOusu1snyT3b2AnUqkC3GWM+yS6YDRTQfGgJv5z63D3dKWiNdCF4gqOkLukOnwc09s1/RWyDorYJOnciVWMIn1"
    "lvSw+7qmWQPtDjLJGhhpa5Gp0naiQdpoTxASeBYk3tzzMaBjdXdL/YZQwkLq11Ak6o7ARf8KFfTQPZR9LOocIawS/ERGMe5E1JMRiolulspL"
    "PKdX090fQl6OsT5yKlGO0MJuJfk2F8HcOnwJfzPWhnRpRJbFIuHN4nXVt0kPk6lKXM5R7EMNNJwJ1bOfwy4Gh3QumDcab1rxhIjQ4Ng4E/3Y"
    "v5YK3nWp0zgwkXHEGZcdnW6yP7lwswWG6xWvvvC6Gc0YyE1XkmRBP/e546iaZW8EoT63ugU6ziU7PIvvq4Bqh3aYp+tzeDpEhOM7bCLBv/mI"
    "giizye3q48QFW8LZ+lWhr449sQ4I83uYf/kv6H7RC7qnLqj3JqTAKv+iciyKQsm4YoWoeC/t/joubYrT1r2fCGY0QF1ITue/nWKYuqT+y2hK"
    "KMVv49KcV3JTWZWxhE2WMCDzEm5mDJ++oUsnar/GymNeCl7g7y9eQIiJ7OiTzoK97od8Rux9bcONi3PjUlLMUulzphzla/aAYlj+oTreooJn"
    "6rxV/Ej3NkfqkZy1cHx5j2XhRYOoy4hqcmYeouWtyD89a3jxY9vfyMVJtrtXlO3uZ8vFdKMsD3E+x8XLD3CCm37v5697G6F4FUKx7ZzKZsUi"
    "/UTieUnmo/CdJnJtlCYNwDRaBldajh6c49yzbnxRj6DirkBdqLbwljvCvOzUDCb10uoeV73pbHhFsM8dmnbB5UgJo8QA5RIz4+Y6W/6SQ96p"
    "PRkfnnFeMi0PyXOueQQ739Fc6CA97ym26pylNei5HqccsOrD8xDrg8WNGNnXaQE7hi7dI/rJxaKsD3M7sXnGKj81P3CpeUakACMJU3ZZGYKd"
    "9lJqU6zApfK7WVqUDwoP0KZssu6n4apKFRhegTt+WEChygnC0FbVHKumyD1IUO0U00UP8GB4i+WYbnq4CTCJ5FID6fxKMU88IJ4kldAbn8qn"
    "DeL8HWxaP7XwbTKkcKzumojI6wcYWvLwcLVkpKILsdz0EFa90TVmwt3c+gnM638egSlmrnkAiZHGmqWERYO2OHIjGDyvrrASl8p/uhr+hV1e"
    "ODdoGhg5dA5hEYDMihpzVMTCccNJUpI4LonJhSmKzvleOy1Rm0vsfU2k5NUyTpWU0zI8tiumIiqnXGGch3a8smgHCehhAhPhd3Q/U51QBXwN"
    "dIdO7P2T6EQOCzBOL4NeSLlDVEGY9r7YakiCaLiCC7tRcoURjPFMLqyQPOIPD00SDpVo5P1UAeoh8y6fShBJF4jWQDjerE6RSQJ/xeSDWNa9"
    "bMp9GYFHD8b0oHQx3L4QHBV+gvLGIChEKz5moNq7Oqa8YtGcDqU4XXQSUsf+RuqwTVRMMmQDYcydhBANbGH6lsus4tYmUH16MOdiIKpLKPU7"
    "LKkOnzyarbC5lMUOvC5EUexXViqC/LMMHo616jspUrKSiuyghmXxAgwWK+/uBaIsXgHVlMLWimuk6VFuSUPVA07P+Z6oi7v247TrFEpgreF8"
    "uRymPNvC+kFS2C1qQU5XCfZXeqKN2pMd5npVAo99WZdCEp2puc+Nc3WVmTD7bI2imQXPOD2wlA/6YEN4c4+xF3wH3sXKd4N74JTDfpvrX/Fh"
    "suO+dykqKI9ki3YQ2XspERiJEzrjKF6OQy0mlGcHAfPRvtocbSHZ++0KZW+dGvw4FkC/aP02V7SG+4+mPT9rcwTrg3+Ov2DpAKx0WTonqNlK"
    "SE+J3PDlrjtRG6T4bEKmUuNroOG0pMET6GFLGgsX9so6HiPfP+d0EkUBMs9nE/+U4JjjOamW1NsUzFX9KBrEdj9oGAGf6AeyZ3nAPcszD1CU"
    "dJCVHLJOMK36Q+ZBbiKiSomocFELD8p9Rr0Zt7ZXVoPMw9KFEET1jqzjSqv4kXlcB5sAtqQ488OKEjtsM02+GCPuc6jqwnIBW2oSw9TAL7z8"
    "YDkaKABMI4N7qakaVFVUejLYpyXAvHq6sDYrhI2j2oqIOEuFtT0orwtOEmYxUj3iQsY/o0CL+lLKtU4v5uLcaWq/ly/qGEkUhn7By1/ndTbW"
    "IfFo1cxTUFjwCnlK8em6iKKcquzxtG1WTHQKJe6YWTvGQcsCzxjCyAkEotSzTgES/msdDMeKyhzVtiMRnA5wHGPhSqrlqZvJBdtUUnFHYheo"
    "owCmQTpeeaoD5WCX5w0/ei1XshdI2YBs5XyyW7dwaUYQqJs4lkrasRQQEteF2QmYCVYr27atBdmTHGv35UM4ltyU+oxTwmPxhMTXXj5Fq1RK"
    "NiIK8Ut/xhXV9hAeTYPbWFzqdVEu9bja9fpZjyQtOntJaguyPq6gNdAzFTwaw/9ERJWwwLxRONeKzkWSM59lURaj5oVLVBarpOJQF1Xt4vE5"
    "mIEacqnZ5KsITeCehBdnzkal+uTphPhERGJv8Sg9vyySPNJlZVs/ndj79uhEMff2eilFfz6dYoMUfVMQga+x7n/weTgZ9ShMP108QlIhYxSM"
    "o4V2aa/K7w6BZvzBETQcvxAoojLqQ9HdlBTk4oWRvAQm/7V/GHHJ2/haBQ9f7sdsQi2+DK6SiLiSPEkyGcYisGiN5gMsTg05mYhS1cNA4Wf5"
    "GoMrRr0vJYldJBgXRKi0AK3CRZZykQjj8OyWxNjpNOPCVVSY2TeEfCofv+M0hH4iBrb/kMRCC1HMEy2Sxm90GVJHGiKOVjzE0s/U9jfCL7O0"
    "0MSDv7dkkwguEGAqlGatSqd7A4pd4idXJSPvaQZT5PBPo2ME0ysmV1oFrTjqf5LyJNb0kOoZKZ5jT6eHAgGY9mhfDQ0FY6MRQ5LAC1il0XXV"
    "lMOg/kkwifNdDDh7iwEnpwFJIZAZ/TV8EBNMwoaXh0YVLgp0kFZzxPjEKmqM2D01/l7AbqSaDOF9Tu1rkWpMEyY46oKmO4sYNjPJ2nvj+4Td"
    "S25dWQ6+eonq7lqIqrdlzuOR1DVUSrmE/WKxHi28mGMwIFa2/BVsXjRfPGTLp3JpgdGzItqBKvu3aBiSpARWDVi/7XuZarE5tnB5UHF/chc5"
    "LNJ0WDyeG+xRZDNjUlmVMUMXeGR/ZxKdKg7iiEbZPhRLiLuHge9tm//Ik5MICgxb/EtV27pyyr6IudJViGRJ3zQ1tFAN4Cy83MvGS0N026Dl"
    "w9FSBpAaNAhOIhVpYwdR/fUaobGY27VyMImYBt72ZtAonnoJQy95DK9R3WuhYfBRIA4VRCdor0Tds2WEgBgF/Zx8i0kECCQaGNixj0XbHqy8"
    "4I23T/ACuKlrfa4MM9WUi+Kldy+SAkAnnBxEzWuZ/DBUrfwICMXSy09U/MaDu/Px8H+gCzAhJTafhZbVVJwjIdArWulUJV0MYTOX5C+2JQrh"
    "ZuBvbouP4ih8sEHh1aNwUhPaL2yteZUdRSM2m6IMxaDXgRbKnZnLUoJIET+SGsT+k5ll/mEFoZK9ZbKdE+Uymw/EwVFbxIIln4rVeirQp2dT"
    "72mpfBzZWLpYTT5vp6HCR7ap6bR4OsbuQ2o6ec5ggYpOMo4p9KRfyFEVboEKVVeuhykO4PSyTp7l5RZXeVMgG+P5JmAk8poXpbT2dV02uTnr"
    "YufnL+f2KEsjxf+oq616wImwyBXQYO6vTumQvWsMBZrZpnm7lA6hQG46ndmJpPBxet5daWbz8z5ZjgGSV1WK5SmxP0vnUHqs76J19kBRWY/1"
    "XXWFBpNYD+7+DfxON57aKadig9OpcBFkSG9yuNLcaDE7GYjJvPZ0cphvKcWQRk0hAaHzvB8gArxarQiwSDJmERnAz/ZfZepinmWRO0Dkpxsc"
    "0qwK6goDb79pYUBtUTRvbL9q7ykDQ7GCSbgQI5leyAEQo3Pw+uAtVMePo9cHHmc3fy/RZ9IiCXlNKf9XMHkHCEbITN51Fm/KNmlWdL2HH1yD"
    "oe5yNLmUng6Zj5JS9+puOE49VtkeNOdAfV1Ek0w+a/QCRazUmtZ+0tjJzvz6szlxOMKykuxWLc6LtWRI85kNY5OMfXO3FzhpDwt/XV2ch9uf"
    "kes0mQV29OsUDSyJptBQIyR9Pf7d5OEY5chb/rSlwcYIBhMB0flPNA6Bxe9RslDs5/evk0UXMhkcGmDhcros/QcvS7dA4ePoNqx8MHouLH5/"
    "w+I3LH7D4jcsfsPi/2Es/t3qWfx++MvL3X0Icz+Fjr2N4zXy+v3wM345BksjQKj/IKa/n8f0d1+ulut7wLZ+9u+ExrfAhdv+tQHlOhLWGWzx"
    "jRX/PYKB2JromguWyGqz9d47gxzizvE1NwFVZJsCWxKFtrCgvirChSgTY5xJzEEnGOuLb4EtevJlBA55FU4FERQRN+FDLMO4EfWCEF7MIKrt"
    "l2jFvKV0oBuIM93dOYLf4aE5iGOv7qIplsKRUwemszlJGBVEVAlmiJA6rrZr2Gw5Gdqvxzu3kF5zGt2ztwv7YBCC/rveboUEZnSfGy8ixgHu"
    "fUx5+MkjW0HY0D3NjP/MeNfX3iJjHa4b/CvGXkd3o16fIsG9wBJjg20UoF8eBf+JphMRcRTTGe0UFA2MKXFxDM6ndLCnryiPldhY0Wwmk6jy"
    "WIqLZ0BOUqKHkrkbS+kAFnFJ1wLS8D/xloP82Kbeh3Mau3Oc+8LdERe4sxC5RgFr2wnigNQFSM3OP0Ba8QJhPQimdJOEGqLIfAZ+pakj7oJ8"
    "GsbCSLVfUHVZP3Z9g6rQE6IcNneQ/R6WwjrdWSEP7/w9G0QyPLW45vWINkLLYOVB4dYPT4iXYjEyOnDNuAleudavzQbmvDvreMZYumqtXS0l"
    "Q29PY8j2Kwuj6KsNN/5GuLGssfAg8iiV34I0Ug3PJZTSJPAAavnaQy2d9W5I5jdDMj+VtnxKP+cnj0aitIbMAM6IKCFsVi8Y+TFpZgl4gb6m"
    "isuheUNdDm3WkvmKKiH5cIuCe6hf15azfPMlvJme+eBoJ2Mg96NQpcQsNLXzfspXQCgPUShffH71Jp6NiipjUPUh02XGybSRADXZk6rH3ebH"
    "0Lq7gDNHZ62QQ5uwMWUHcw8gb+ZdAxJIIHUFym+wHowo5dpDl+jhlML5VhetLKFlWpBc7Eoxdb7JMHXaZjw0cjrWOGH3TAQw7fp7Rep7L8im"
    "a/jUAx6l/uqKTJ7vPqoQK4pcduMdYcLhbahxO/5d7PPTC5kBRn7UfBMmzQRi2ixCkuwzN5o5m1x4k5pUEEtF26Kswge3PoK6P/2IioDquQU1"
    "0jGYnsaUzWrjFG5Ht3ECl4mkq06r+Uuy123WwDWnsfBSdKqWXFQxBua+bTCYdBVV4Ba/C+zkolB8JQ9XiFmck/GLWf6cTFnMg12+VBlEFtYO"
    "AN+EZ7cQhvizaLIGrj9xZoMkOUjy5QYSNcsijZb0QuC5EMcPJVKQkMVpmJBW20wDi8dZubI6TyRhEGMfAlFVwWD+3tqn2l+dY0h7RI7064dW"
    "U9U8MJ1EFEr+ZRhHanWpQ4v0vrU3oE5wg21LYJvH2bxEkx5sloXySBspSvWi+6FFBfNoMWmO5UJM++WLF/uf/EKT2YmHS+7AeTab5uk6C7Gx"
    "TvS9VLqhp+/lrr+NrjOvT4gSqKIqAQkp6WXYbYX7z0Wk4leP67WLNoXK/0s4nhIEJLcNt7g5gSk2Q92LgoKzuniJ868cGE9Zp5hMbZuFr9LU"
    "dNKPBijiwb/+ECqffDtJL1nTwM6nZ52L8/NWu5sUq7xwUi+iExd+77bAe6d+9QpcudRyMQqovpVK/ozKZObhFCN4aoNmJdGCVM8BxmPSvCzx"
    "SqGmEMIRKzV+2HWDZFUWEuHTJfxtXeSih1l0vVlSwt/xpksJFFLlGR4ixu89ohhvII23bMIi7FLtQVdPkjWQniP/FLik6Sy2GpRKp64B4qm9"
    "6qvLsZWCazB4PAn1s+EsutVvQY27KC2Zk18wEJL7PAAaAmO+vgkWRfp8VWPF+L6sUvLI4YQblH+eKK+YvrbeBtv6E/GODHnm7qDYZid5Sazk"
    "VrP2YLBtxNsgF6dagVi8UISHkUUTWAHME+8osw3mww6ga/AIrTYyeMmNOQtwh3GGuGFGCS0kbhgvpseP+TZGkWP6XQztcn7C4DC/53lZycWI"
    "PPMuKekeUYOsJNnEKhNJvnbQVWKjmeO/phKGhdefoWLm7qHoy94Npb/8NY14Lbo5hYL+MLXc/UkanLsXJdJZZHIVyy2MTzple0HE8r/49Ykk"
    "YCag2N4ce3bapFAqUpaNSWeJiNIRgyjuT4d3GboTOjMVeXBpmRriJWop5ieHmJkwR2rnDTxYsW61buuSghN98jlLCp7OlfOxwjNke8FNj1uQ"
    "Qt3my+EA5pOxK9uiq0uAVbyZvQJGYnsR+hkCta+GUwr8Bu5LU10C/yZzTAL5KOzdi1YuDoJmn8RC0bWgIyoo26/nI6Dyl3WO61xlj4gQBLXW"
    "6r9t+cIRVoKgYOTpUBC+qv7w6JgpGxcpGILh7F2jBvZEWc6iCLJydShj3Y+Oph7b5g+LtzZKN5E9xLB5kGLV/OHJrJoZ+/znNR13w6AwQUX6"
    "hVVeEqgZURj9FfXnRHPkc2pMaBshRSbeNFRnz4FNvty6aqOJQD5t1erNbJMj1jSpH18Q+LJe8xeQBtTEUrCiv6hj/jPrnidjYhaCxJanRLVh"
    "/2OC+qlIPxvXQJlTOLX16xlSXYH4ZluPVTas8RQ4reObWHo6bJ2E1ipy6qPaKy7UO8mHqGabmaXx0KrVmoGG1jjTDrwyHPT3SDI3uUGxx0Qx"
    "O0/PNHWTZhBHifrl5IEOuDPtfIrunTsOUYaHL/TiZKwMWNCV6UTUmEY7Ojydj9HqSNEy21RqGoerCDZ4CXJM4XDYwAO9Q2kajpHQr+6UjABq"
    "abfEB6Vkn2WaAGNyvoNCeNbVyd7NcJDRpkJA+eKs+gtQaZ95M3uoc3fI7MED89ICZTogiK9Uedh9wIXbKUDTspYav6tfPxW8rvve66qL0Cdu"
    "qrt5g4gUbVywshrbshg1bNwusy0hIqDxeA3QVllvG169OO5etDFM8Jz7uDcU7uT3SdvbW9zTL4qotbW/0zjOYjnkSekii23l4WRChN4zu4Ii"
    "WD4m2nAIAIEv/gROODQK6NuC8n6aoGxznlIeirvCszvDQvW6198xlJHCEaI5HN8BrEK5Jiynmaz1+UmgFWHUCFpFjczLSS9tac3a2bfFt1gr"
    "F8XFrWtk1Jsv+UcYHR2Nc0LLnkh7LjY8Bat8u90zdgukx92o9TnWtqW8T5hBydWfMhUa1WqprBi4qOUqrltAXh2wz0ieyo26dDOG4U/s3TYE"
    "AOxQwtHvin+rLk6GPwb4KTR287gAF0WPnCZPnvGZrDMVwdJ7PiWWui4OtXhvB4ahv6Dss2hVYqkxgPWdbrV7AUA5JnJETRIwwaZZhSt6InmX"
    "pldyAEnBaOMXH5C/6+/pwuMO/uXTBwvf8ocXQzfjhotTDMGQeYd9lNM6shjAzmr9pBtJcez+GmUn+31mFQspREaWUNitn543sQL7c8RTTe+F"
    "dXMh9ErjFvmYlvbmoyGd6lBryfYbnHsOOCfN/FVB/EAWQtkEkQbEVnB8hIahwIs5mG15Xvdg7WJSjo23i727Rsw92GDu+jEXKwmxE85AxhSp"
    "TQm0Z4S9neopVgvvcJ3uznHLh6oFBMDHERgXR8ktwyO9QcQnaCO2t7u4a08jiteQsnjPd78R0W+m2H1kM0VSlSklENE1TDjKxft26+Kc8xCE"
    "QdFvoMh4Lek9QBKx4iZjy7sBpX6RrlsIRuwJfeEx9Popdn9DNi226EySCInRVsjEm1n6hrdZ4QNUjN0NKXpMTRePtXFm3Gf++RdQ0t9dwGF/"
    "9CAVD8l7ywlu+fkM3D6O2kpvrRqFZr3ZPDY11A36PAL6JEwiNho5j7PQyRladJZ89LLfXjGaEc03q3A+RUvh/x3oJtVMh+nVWnUmXyLtCGWQ"
    "qinkm8wP332HFSsw5YF+aWCRinaHMSMr7sD4pPhSBz+V/BDKKwm8lDlRxQ12q2agBxuUfBQKqBNmEAmpHg3hhRTXNIKJnrsePLOmoSk6wuEt"
    "KKACXVbEi/ISG0Gaq0QqlUFlKpAbnHoEnErzI7gIZWEcmioUCij9BaidY4HT1YQcNDwzKBKV9+WiPWoqnZX/TDHUjGTe4OVj4aVf/1T+Ui9u"
    "4sBUNps2g4Fm+l2fcpp485EIoIDnYNInfApFjJlCuzcbtFsL2rEltIuxBiIDBSIPyVILov4HQIcmECykk6pVJz1VFb2xh2KSQqJrgyVJWQXO"
    "Ql9PpFIuJssvYqlARmbvLJk4jdtYDzpT4CBj8tsNJq8Fky1FRWJrTeIhoiWrKmfoggAkr1KfZWG7rNVPOiFACbmvjeEe3E5FVs3FjUXAKeBK"
    "CfXJ4Ce+1KAeYmm6jZhR7ANeapw1HkHnFnE+lR/5Hy7z/2GDu4/itNhfPAJTpfaYX1zCVSFL7VJT8Aw/xb7hp/B+O1QteDFRSTgKbA/FQbaH"
    "Itsbke48SHdFPFeHw+zLhAProcDxNBFYn6QntQv2RtVTdQE9QoHTTVdYAaWAiG9YWDjp9+dTUlddArEmV8J7aD5QbYpobb5iKgM5Cap/FKk4"
    "WJxUJKC1OJm4hlK/4M3ktA06Xi+RODCIRPKMFIEAr8R7DAFoJp2Yr3KcmOp0dWFgD8lIftsIzW+qeO2U8muc06jCjp8DweCDgrBdzLVTsbvy"
    "V8rAC2/nUNr5EkGZJCDyi5g36JIO+Swllke84tAO9XyZcJ0KrnfjfnxkSvFqcUphn7rRmGlBcqFOOrwGfIA/SboI5bEnCcerZOlrbf7yhZUl"
    "hYvXDxEuPsoimTnFrp8haeCkOMijkzAPjGMKPg8neCW5DAN0uSsTAQGx4y6iND8ovDC8xRJNovICp7tRkZCQMTJ+IWsqieyb4LtBdBXrMw62"
    "P7wqvzuE4mFXWPaIc3YgfW/Un49oOk9KAKEXRSam9QzLjyxMvF+ARIlYrKLhhHAzhFxMvS6ZMphYYwdt2mGP3xJRo8i72rNNI/BQt/Ta/3v5"
    "1C0Lix5G6oz3QrplIVQrSqd7bzZ0b1m6p1KGVaIvkUHZyBD/2wO8h8RfkdUsc+hFrUPoYDuEu/2fyBMvIWw95PrmtwqSJ8+bWLOjdQZCa7Px"
    "b3+m74NkqY0Y9Yh2RSV2C6ZmpYpPI6zkMp+lNIlNNhkqxN8Sbz0Ksmxith6HK71O5Ur7BbiSbKP1QBbEzbRuhzHVpPQzntffBuN56pxnv7gt"
    "695CMmxP/lFWIRyD4BJSZvF07kQyLtVBg2KisuqFWUYa902lKBwjoEi1hSq7okgG8ixOmgzUzpJU5x34FBBtz9nbRqa9ZCEKPUpcCGdwEUOh"
    "U5ECr6io7SVKobP1BcPN7VhY3oT43RPkqHf3ac28TYPFqgyxWBEIe5LnLEPv779b3ESQQB0bKwp00RoNr4eXQ2xdYlT1h6uBiB9JD9TN8A7K"
    "QEQD6njpJWH7tkeiqdeCkqqqk8arTFKvN17q5e7OW7ZBlHM2DloFmH2LYjQSowiFHCq9IyiNqr4D1OpuEg+h7Oc9kDhU6D9HqSla59XuB85T"
    "lDJvet+ZrFeK0J+FKIP72UWKxSg6AE5iTF+zizDlF4WR0Qbo7l2i7FPykzYdAP3SQmT8Td0DO+4sWYwRs5ys8Fpv1ZiSnjBjslq7etIN917u"
    "vQx390LsBSMy6r5+9fRmVnW6EemgtCyoymykgsqRkDE1nFHhiWxMa110O3A6DNlCiOa8URzP9jZ49k3ima+TWipSZTQmcLHJGlocjfY3aPRt"
    "oJFHWnq5uLDkJUIrCdLwRJgxYqgGpIjpqkQnt8b1ilEvDTFK5nnki09vveKTD+6l1OP1yFZqKMaPhN+6rpje2j2VBMmPwKi36USIojSdoQ4R"
    "gpLBnfpGTPrG2dcMWqcZ9TO5hiV551IxiCN4P551q7/lIBAPSneg2Si0kYC+TRRS/o/Z5E8owB/91Y+iQaxiR4LR8HboqwwsLUMXFHHabJw2"
    "ujn4JIYiEyFyLd/JRKuNRPSNopWsNIgGgqiH7RtkcwcSftLwSUdwYeB1DkbpwSLwWbyTiVEHG4z6ZmXs3cW9+h7VDNwWLamb5YvaQB5hzX0n"
    "BqbyBzRoCJl0+gXn3Y3g/IjhjtRzUDrzhQRk1fBO51gtIQSpL2Wr8snx/ir2G0n6W6cue4t7Z73YYpRSerC/Q6v0GClEGOelNnv/FGrzrMOr"
    "R5PJn/M74YQK2N8BUZRIEDwi8i/cVs4spgKtilICGvMGL+Tz4GZSob4OfDmzjEhMfUTTJBXSSU0xsFoZDknMapwNFGYfDVb9wbTJt3y392CZ"
    "MvUemC9uf8vfif/OmukQjIziVFVaH9wCLjrHF8G+vD+kuChxIrEzns93Ra3v6ewHUWHRfzXVMLhbHbsevXs//ZB9/JvaM9oawz9AJKDDATcS"
    "ND3rD+/ATlo0qeq43aLEoS71hWyIJHhdFBw+lI/kbNRTTB3pOhlne7LV/ENvkf8Dglh478kScf+Y8G2kimHoBlZ3MsCyeAXE5Kr9l8QK/ZcZ"
    "QgnORim9Fk7DGrEmQaKv2d6u99q4W/I1M2Mo8EjjylQfnCtkTqyX8Pi35TtR/F/Iz+herU17V7MAhaby7h4ENPZGXllaSmWNatMjQ7symxjG"
    "wpEpleWVWs1qPyYWv/X8Be7V9XjKk70Ly7+e5k7SVYTYIDJygt41xkj7MAMvtzoAP3IYX8zBD8QLxt0lsGMvJQkjIZrr6jvPHGH8aRY6Agar"
    "jTLvfT4Y1Au+gxkq3w3ugWcM+23d16snmq5TCD62FxlhqP3rH17uQpx075qAn4ZCsGHcfjOjPKpWZ61qYPzaSbv6XmhiBTBp/xvBDBMqYsvP"
    "Czc8UsebxesuazgnbABnRjDqI6jYFY0YSYHkzXoEEp8SnqVq62Hfvn2PchZ14KHRKxBRA10JPDXFPlMQtKQ14MCiwwZSw0p6krQ4NiZRN9U4"
    "nWxzoP0aNzo7lr0u1RybCMUlyUpBC6BXgqFi6oAvBnJw0yk20ADa0P0N1HvBNiyk/ye80kMZZ4huz7tojAClt+MJST6orkF4Ru8eBSMdns8K"
    "f0DXaCcXz/zEKxvXCk2xCVJcM6rpKV/IMkgDU9hRdEuYCSGPmmiURstcZBHuTIwilHssSpj8r25CENeMJIZrylWmMJtHkqo0FUomiub1MknD"
    "gsLNTJRPfKNDPTECeYTm10Xd3XvpDilVCHGBDPbFBeYzC6eSQvPrNQvNC/io7KHrEJ7lfQkp5CqEPtmALqOIrxzkAfZGGJx7X1Zup+gvmEgE"
    "aLEETLeoLCQQSWu2oTEu5BdiG0/5CaA0/X50h9f6ElLxgor++zNAYzLl+FP1Yjm+i/pYVH/nKDDdGsFQh4TBJnvz2c2EMoZZ8oIwxGg67o2g"
    "r7bo0gvkbjSafBkBL+SGoekYZrlPJJLJz0tpK8R85SmCahqRlUqkECJ2VJuwWoCblTgJC47vx7C4GHL4B0eoGmAzcJFWAlkksH2Agt2HvDcD"
    "w/TlHBugzlj2401Db+HA3IC9OSTfj64PWV/8PvbuYDCJWAwR+zxEqCiFyBCLMeE0LakUf19IroEJjwhWAvXzAGkjBs0S2dDdrr0GlByOwWED"
    "jdt9WawXZ4vIShZJyXwtCVUA5Fwcg663uVwObP23cy5CZ/ACa053gG+NRRuwp+uV5JjsjRNv5jNnaPCh+Z6nAHkRxgzVH1u/gocDa/064MCW"
    "EkbllaK5sSmrkkVfc/iz/fZD1E/fjVQEJ54D3Y3jqznSSPRMUqL4cFxW9NIT1JQ0w8N1Ez6bNPOGdTdS5UbfjTAHZ96D9Ftgy5Z56C+n+ZRn"
    "yrdWu5gIar26QK63RlNEy4UwfGWip72GAriccbcWETvfFrXV7htp38kTWlrk9AoEfrny7XrkSvNdnzCpAf9NmFrZ6BWKXHrcoIjJBpnumupD"
    "zu6hDprZS55cPMivR1DPgqomQb7J7R2Ud0NfPnB1nKEU4HsoRKiJEn19OvX2L9SM9vyia5H71EJvBd7wR2QW5ZOeTpzWN7P7cT4tO3WWKiSG"
    "Z886UzAwgXH4q6l7BLMvw360EF5ZtUaKopb1Ugp2ybvfOa7DrQZAVNvtKpbHqdV/K4p9exvsexbYJ+iVg3/8q9SB4F+XgAF0qPQgfkGqDFa+"
    "5L9z8bLVBvXgjFMQKCYkByV94x9A6/Y32PacsM3PZsnjNBe5U6TqSyLYC/6M7lFhtkUnBykrmKUy/UwSNMrfLMrTPmLSPFDBt/m0xHCyM4F+"
    "AmYWiNIgxb03C4wJvnffPApYKvhyMwHrklwoWwxwsfAHyn5Q8+o+cI6PGmtgeKUsZseL47dHvctoVBagy71WNFWz+g46c6TX0yvwxlJXS5Uh"
    "8gZrLnA4OV3qN9f0kbX50SgZZGgfl0XgZdiclEycocJQyyUhuSIkDodLET/sCm/Px3+OASfxEkIRv1gK3/FOsXtiXrkit8QZ/0zuyKv8O4KR"
    "tLoHwLdwVfSKv0WuBk6Eq+EoCmWFEVbgDQcSnNN9qF0HpdQ3xJ/gEZkgYqSPZJtZ+vN5HIUQtQq2BzC1hWxq437B4WQMRgSH9fpnESqvddnl"
    "0sQKKmpXwdWod50lCCrPLhsi8rTe1OEPEANfb/jLs74w4k9Vvhf9fnE6kiNqO2MdvJYmZeAYMDgQg9mhqAvQOBadIkgsi+4WxeLk+Aeg8ZsN"
    "Gj9nNFaQLkRkX8jhZjJK/TdAljOwmFePj+vn3SpGOp+3WyeNZj2AoxrHd5PprDithWKcZ53zVru7KNX1vfgAxH27QdznjLj59LSAip4lwbOy"
    "jJ+ZyjSJcXkMnkGlnqfckeTK/Jr7NtVBoH8DEuwoTV588oiaHsDn5BJEXAUVoUYGgYXrwVcPyb5H+DeiNH0oAgkKzGCg0KAMRDoNLpNN/5hh"
    "eYXee4l8JWEjKMlIWbwqyINUnIYu5lv8Ep8Xs5/lvfVM1JgfNqRgzaQg6e882C3q7wTDDBmmwlHvC4aQUYNYRB1yMApjLbUbxsBFqLP9QTSS"
    "RWcsOxZgYUdnrfBD/aINu4UemaewctgH/givVTvU5lXE30gXA5Tw230NKF0jx2U3/Ln+UTkahQM23ZdRtJ2fa+jIY2UJZ+zB7nqcsZ77UcrW"
    "/ZNNBhwre3GfLR4ohDhcMNY9m46hwDAG8z51sEpGgxFzwvKAvlAwZDn4LBHflSTJIHrVLo7hgotlWrFLWXakzBeLBFJ90xFP7u6/9TinxaOW"
    "KMCU8DMvesmFVWoAUw6GLRj/vpfayM2hKouEHnmMqYUC4K23TtqtfyPBEeaf5XpOrDAY3sNl4E8Sn7LxL3ELFolI+qEohwaz8M1uOAH0nAKE"
    "6XwyiI+s7JMI76WI5dprtKinY5Z19tnstPJ/KiLCxj19pNyzCTgfQkmk4hcgWP8H4sJZao6hR2Mv8OgkzknlLoB8jXChUyQGZ5/FhAZve0io"
    "7tHDatT4wZD7PM7jig56v79Dw6kjHbsMTAjT/qivH9YjaCQJtwmxooIFy4FJ8H4rybg9bfWmysKBXTSkFzC1t8tDiDHbbm9Q4AXjwLLDy/g+"
    "j/cKVnqholPTTDYXQBDBS2WNXbKeRJ725zYJTUF/qztq5UduXjEIzZ9DvIM/+WLQioj8SY3RAwRETz9P80HMKFn3LGWoBzUgfZjgtGAZlbv5"
    "JeQ23MBtkZgtro1HMrL76HqvRfJWSCIGGzlHenPW9QpI3sx05510c2aKkJTAPDUxYVMqzvkXw+8UFKYsrC0uS3EdNVk9X4pPKMhVG4QVShp6"
    "KpHK2lgBQcp7f73COqQ86X6Pf/5EHSmnA5lxszyiukR9myem7Hg1V1pavHsm2VicPboo/qa3d/7zp8zgOIWq6vPHcKipaO4f/k3j+cM6P68Q"
    "tz12u8IdV15roVd8IIF1Swu71tXw28Versku5pMCSlsJcpuO1HLSweQW7j2eTsrYwy10Bdzb5AXqGZIDL0FfTMbmEJtS8GcAdcQiEvaPlBsD"
    "DVK6xZz0V1tfu0NjwlyWegZJVFYdjunk0LxQ1l3EppM/OLiLQyAJ6XQmIy0lpl6bkzlVkUFIy0ogasViHUc6pFEVgtW1DYNt7J+6HxhqrpFC"
    "zhZyaHKLqeTdFpUwADX6pBMCLrYb9c5OSU4qNKCSsp2Inj7yAVvuSGQtC0KsE7PpnrnKiYUfT5WogjfuOBTXAD+A2fRkCMw0b2IXCjgGcC7F"
    "sk8q7t+IVI0C1jvLqHeWpd4ZACWHgwGvUxzNfPYmbEKBa8UwN2HQb4VilWTaB2Z+fNG86LisabFXXSunCwYYgrXRuOjnfMRNK8W05jOzl7OC"
    "is9crx6qFOpFSw4JsTnR0XOBLLqViP4CVNLu8k3ZS3uBOofvY5WVD9bSOYfjJINE0f0rcRZeiUfQKxgFK7qZJaRNahYKxbbCrYH0yncJi+IX"
    "ptkF2BTMRigYU/Ro7y7Gu9Ojrwj3LFwkaiw8ppXgg+9jlRcO1BGNNfRhq9k5Xj9104DszkfZl63x/gwa/rahcQeGldY7i964ou8vce2YROff"
    "ucqPw5+K3rtsx/EiZjT7eCtpx7tozafNXV/FXVeGMjA9o0zTo6s+vppMb3HbAZfckFcWj5s4uyfBoVanrLLqGTkdTpCjYvATl9XukPhK9sSE"
    "PWyRF1d+OfS2Q2PbstLIIhdmoVpUG+R9OPLq0jFZEpY9ymxpf0/P0W4wHSLaG2eZdPEB+iHtbtRCU8ZxaH3KqMcRpMS2/IKUeJjEz4MNfq4L"
    "PzVmpeHnHUTpg5Isg9nQMCNeAbB6gpnRmNFuIKG05HfZvr0NcTyNNrly5LhGLSGSLDvJY2Cx2q8PizUwElj8aoPFj4vFGEyJpVSiGUGYgMQu"
    "FW/KGQp2KgYMe6HDD4iycnvyJ+MgpWETNHLc0gWUNfv1A9iWfsFYezAtKUc9/KfTwa1Gf0X9+QxrcqPdBJYWDuMQSHhoLnfr8Ko3iiPsJzOy"
    "C6oAFov8eDJbEW5i3BvZNBTSE6rL+4g7VhvQSUHi2tJAwU5CtfWKuswCCDEdTmnLqkfDeZwQ8qVr6+sWKhCRhzF4aEmtJZDXAB0OOm6dnjfr"
    "3bourF3jpH7ymycqFPOSpPUIdC9hFKMTBH0pupW2MG5Cgr8rxliCMGDYP0XUznSBAzbolSgpI0HlehhgDOci2TGe1SiaaZrHn4A14SBl/VIa"
    "mu6NIqD+fRykQdhbVogwy6J06rDpkYdCLvLiY1BFeZ1cguheIWUp3tDC9XB009YrTZoYd3NHMeaS22M3AXhgCZffx1oQzeLrWoZEcyssueOX"
    "NQu98ahypwx3iRfIfdrg6brUejzO72ONf/K0hPUOkiY0voJ6T5UmlSlAnU3SE0qET+GewDjJuTrJSJe84SvX59nGBGp7JbH3whT17QZT14ip"
    "IqhOElRRr6MiynwkTLZqPAXhBYb7k3JFE+VkM9J0FMFsnJ5edKue8vbZQx/BUusSV8JkFXeof/3jp6Jk94cNMj8mMvcGVNAC9SFpMBee7abi"
    "yAqIUqnpGGUHEdoNimJL/CYCAqvv4Y9O1/TJvm9XT0+r7WTxMfOz2uvCvSRQahHCvSb1vuX7yb7cTGKZnTAlzLHgSxMQl2TQ1RKhBtKFHMWO"
    "vU/l7JlR/TEmlhiJI9fT3u1tb0ou8P3XWEKa71gZ3RsiC7DMfTFhErCNY04mJ6ArlzoGTLx9VHrAdEBVyMb7XxHFJvXaFjME7r6kEA1018DR"
    "k0oVDxl5P21Ixrr4H/sdLbcowLNZr54hN4M+qnTvOxfNbpZVmkewJzEtzTR39GNjL2+VY/oXw9SN83+tyVJoiAE+oY9PZH87uGoip5vTTb71"
    "sUmMUe8Q8UdOzgfMqUJ04gq0H47R4Eu4whFuGjWGHrejuYwQgACGNK/GnDHuefhnchzuiwNK3J6NO31tt0cgUoCBY7L+piWTgHJDxuoZpbR6"
    "w7vA2F1vc2A2ZFJ00BisSTdaewEa79gy6aL4Yq8+urQCQZ5Tio0jcUV+TlS/WoT+b3zqT4fBokrYf5h4s7dAm47YSeB62gshNft9hGvGdEkW"
    "wOqsd78dtN644tdaMmOpJvK0Z7XmJiBes1DkvdCsjLZT0qnjCbY3+8Xb+FoPTbFdrAI1YSHHwNN/ieqLnXqTAqYSkfd73sh78R0zqb/T6Nb9"
    "TeRpqI6vNmo+UuXwR6pGkbi5jxyxPZhDgzsUwLThRGRAu9RMmnPQQ9tJqdSeNqgIfQIyOzJVNg/N4vnO6p3OosaDBamUJ8VI46SBPlsbq8E6"
    "rQZs/BlhHGL84rb3V6jON7wzVQFQyfpRNPAFbJ5Wf1NQ74TnoBDpg63/dlyv15JWhILvrAjJl7OOUSBKL55z1zWOWpHFwVSKdhNuDpCi6hmQ"
    "IB0H0sRobVz/cArKldiFZTwhFqDIlyVhO833rubjvmxyQ10WmvWz912sRwylmKSOB/RqdFhJFlQAMYOUO/OY8U38B1D2PsRVQ/jp1iFogZH8"
    "OUVtNKeoZGCKAWYMUJG5d906BJggJ1K1oYw4R9E3QoB7oKNgzMOQKU+HKYTj60IEaW9DkJ4fQTJYpxSPA5+xRsvyOhorXd63xjwZ31Ty/mKM"
    "c3+Dp8/Q3aywk5o5cu1gjH+4hPo7gZetquNPUEsfO5W4uxA/LfDSkzBUE/OzOCo0EoN1szqOysmGw6YjzbIsFpv2TEMRh7vrZbnmca2W5x5s"
    "aNk3ogQATo8B4xdUAsAxcka2tUWIVu47z5pmPQWNEiAD+8kFBXw8OZXyIgtND7elN4JA9/vRpAcB3pj7i+HwIrZ+WSKWR5Wgu1Q0xWiQUay/"
    "iVtbjFy92pCr50euENNU5jdlhFcw3aAicA2yhANREsJq6J2Zaa7CmCjlPEncOHIfqsHAccMFp3+cJeP904ctQMLwZnuol/h5Aez1tTqRpGOD"
    "sOtDWEBIXyd5Xdejkl29I4mOCsOAYRw3Wx2sfiR/albP3l9A/p2LmwXfeQpEfbNB1Oeh1E4h2UTwTRHfXzSeXyXZaZtu66z5MZmhnzbsKfDu"
    "7Qbvnkd+M2YLKsS7mkZRhQqHUgUoNKpQLC3WvLrpDSZfCCtBGEXSqTMyHIRs1n+jUoRUww1ONOx8qNZgQSied46r8BsACbg1Ov4gnCXRDXCJ"
    "958ChX/YoPCz1aGh6Qn8TDHxUFBtdpOjPEOnDHDGd3DnNWj49CFTa84avDI8fKjaGw0oeqAvp9hNasJ2bUVSahtWJdFWp+vRgGkgbfzptV/3"
    "mG3bnMzJbp2QKovhA4huAsLTCRQtohzqrcOXplqr7rCpyUpT3TKq7O7LDaV4tpRiFP2FxR5DoygCnMUM0yyzaYbkUkYgDXikurjMLOpR7LXH"
    "oiPMzMliJHF/6/ii3a5T3Sa2aIkxWJthiatdMQDJM+niYazdL0rJgADcO6QMzmyGoVurp25CrDBOB7OfgIg8E3tfOrqui/aVtuZjJjRU9s2P"
    "RV8XTg7ZEMjnUTZS1LylyozCrGdY/Nonx69/eLkrh3nymQTeQQMlMHA0Q/GCP7swb/BTSPW7extcfBa4KAoMgK5X16WQjSatlKbk7+mhFNrU"
    "MvA4a3gBTe9EYRh/owDAytMG9IFNqQ6/8CRPgs/7G3x+HuFVw2tg1AFKDdC9NBoNdAfswT2Wm+kHWp0RtRKM0p4qnJk8K9Gtxw7YeA+CZHiK"
    "og5Vx4Z8a3SVfYTgZYCaVlsTvpOF3nwSJD7YIPEzERDYXRK8r3ehmBcYVgRFVngK1Vd1VWbMK+JUYQdXzbLJ1S5Z8XQTJSKXXN8NEj6Pod5y"
    "kgQvM8GTYO6rDeY+D8wdS5Skkkqil7RVyhwo7/UYSxNiMpysQp7iAdTpO4iCKdUzMkc+CTZu/NLPhY6iCQbr7DM5lXiIDj/IuGL5NfIGX4ui"
    "D9hVHMwXLF1ipxzQ8DvCu5yMxi720pOg5MYD/WwIpI6sVg8CNBVJCsnI2htBcQhR4CQ7S1ilDOK5hOIVdOgBV+5+aIgA/tRE4WKvPwnSbtzX"
    "zycn+KBoTvCemxOs4wnh7FafEnwgCgZrG67soQvAKJSE97BMsGJ5CQ+MhS8UR/ywSNZsp+uSfkKclLr18cJ/aWDmdI02wF6JhT7wR4yGeFr9"
    "ZyrBNaBdsHHc+Bjcc7QKgXayxC7oI/AcbVzgAjB3UsSr9ED3wtf157enBRiblNZNdMdn5r2W7MT09/hT3K10ds5wL9SObN0p7mAlf/vm7asA"
    "omLKe69eY5knVcEiBnILrKIfV64joGVAquQTsXK7FidbT/m6sROLrVSeMNz3kG/XhsVCZDgyXqvowMVZ5+L8vNXuJkVP+RpuDA8k//UC/LxQ"
    "zUz0KSWr3BcG1JY//rzbgisGeHycE3r+tG2LVayfWKgsT/9ttTMqS5xVtiQZpwYo31M19nSGzA0Uqh9HQ2ol5pTR5CI3EuggzVK9ZDFxeTIG"
    "kVY93P6w52kge9oA9gPbkxgslXt1MK6zP3/8Eqi+YFK1+3HljCiEuZ6PrQd/U5f9jYikr4uKpPtKJE1DEwiF6AJCEL7ky6eLkDePxPp660mY"
    "vE1US5lY6/J7d6zqf72WSjYiBjZEkU99IdmNirsoHhqkylvjlxou2sWwMfQWwkUgGknPOoiuelhHUL12hBb3sd3nQ34yUUH9hfU1t7Kd4WYa"
    "sH//8QSZtErHRMYnQQSCSk6ksS5GL5p6qII9gvomuoIUeGEJqiynZb6ricg32vrU3s63WQBV9kpQveU5Cag/giqoA+o5WhkOKqhKwTvbFU5U"
    "A7Du6PZy6fh2Bt2TYVuNY7ar1nTjnjSEy3zjMTBub4Nxa40sFTjD3WwtJStR4/sFmCNgN2AjoANPxTJcfVhrnJxg5+6TduvUW3Hei27FXn0M"
    "vNvf4N1aE3Jlwi0KO9g/eab1GMHeE/inwqnSUa8L51DvEtVqnOk2bjKoKQ3t8l97DJQ72KDcOpkrADhiX9AcGsaRfKhC8DA6CVceB5+HEyzv"
    "IPrFGe0NsjEOEeKiw/0CdTAdxIW3QdnHurH1ZuN9w9Pl5QHzPAZOvtrg5Ppx0sjw1p+0mbFivcaacnFSrEZKbKgrUP/3PBzMeO8xcO71BufW"
    "iHNSwVCaQzCYRLLDOnXAxDAibKBgoKUo9FQQ47hqDrBP2VW0GML5XnsMfHuzwbc14hvHmCtiYjBV1FiR8UKb1ckY3XccmSnoXjqyOTMid6Q4"
    "yjzyVuC9x0C3txt0W6cbpt8H/zI4YVh9oJYvEPLQSzbzE05ECFEfQYE7rMmYjnLV42Pwe9dV/6/TercKGFHNxbkiLz4G0v2wQbo1+07eFvWd"
    "HCjfibLmWs1JL/SZ50X1uBqyp0ws2PrvQ9Pcjz/pvhW1+kkV/SDqwA03gOmqS+mmarxmtzPFBuAeR83bJ3DUqDaAKS0GzOfhcwu1SO5epAZn"
    "uyjIktyLoxFE4wqVV+Y+xoHIdLjt3am0ycHEFAC97d7k94ll6kUoP8EUsm05hTd1rEmR+jPo0J64jmcXTXKWyrWHqZQLgp+O241zLEX1rgoY"
    "AZqxTbXkDCbh0j7iv7doX/Pp+PB2Mpz2okNgHHDM5Zd7gLb7h59f7u6Xr6Ew75TbQ5a2BHWG8wZCSZRWGOHhx5cv9gjjpZaWtVqICAPowKUX"
    "2aMdXC2cRaGtmjvEd9IDKdQrMlm12/q5DtF01Y5MV8U5rK5diQhLumcYXKaLKdaMeCrL534KzIMD0KjZU7vRQTRPah8SKe8A+WUHMWSA4t8q"
    "twyoiGjw7bJkedr8NfRKmM4DhYb+cfkoqN4Tphh6vbNByv8NSCkopcgft8s/KguMfJqBmjIx3BDylJchiaCe0Rs03aCp1z2MTNt2DY9V6dKr"
    "dKKpv2DRywMDHRND8nFQvbJBu38w2iHK/Rnd51BDHgKiJQzHKnxhvzcdYNAjnqMXH2WgIQEYDij8uf7R9ENYmJkyeIOjGxzlkCzEUln3xe85"
    "Sefbqez6tYGFS3HpDfb9I7HPY/55U9T888ow/7i6vUaXIuYf0ZYZtvuHSBiQDVN5vNcC8+Yp+j0aMFemAdV1wdf1MfOFYhGyflOM/0Q/OXXY"
    "IA5ZpBEl+81gxlLrPdhKPwDoqp3junBlYbizMh/xgdPCQmCMOAuyryZWNDttQPViluZ4AxC+6ttQSZmbTqv/Algfbm0LOAUE7lJg4puYQYwo"
    "mZmw8HgHMZwWQt0334u2CBjtcgmJsmg+vFOffd9uXZxzlDH2U4Ax9Ip6wtYvZsAa5nAr5XrhkS7gRtv9hAXoZlidD9ElDntX+IeueoeRN3U8"
    "lyqeeh0q6GG+LCMeVgMcTqeTadhDOzSSBhArGFZDmIvPCusfqB4R4wml5V1GUNUjCkXyI74tDaF4pKNoporZxbPJnVyUXZCPn3sR7m8X4+CE"
    "XLCXCsRtJ14rBdZB4ywqJglshB2CNr/pUgQyv9L1r4hid2wjFpa9gTAWzwm5K8zcQoNAgqWXrz4b4dVnC3zPvkEEIw5+tlvYhoxEBIfsb23T"
    "LToMdlVweJkyokvBHgTrfOE/jgIaFeweOigvH+wdBgsvOijreHThR6JHJV0vhoPW+bDgDfhDsC08LXHX1dHjZnZ3jBudbkBO3vLETSaPirgF"
    "mAHE1l9hTW5AJ5Q6ctOqsBYDm8SqMuhVN63LWnaKIIsSHWbCAAfX6aqsE4VLolGZTqUtadhQnxT4gVCtTCAxkwgA5eY8h+ZRUEMKlYL/RFsJ"
    "Hvrq5RZe3eltD6PnhUFQ8jSUdeh2m6bzxTcLZVGpV+AgaJ+dVOAixLOykhdk0olK4LqJRpBpFVzPQZeBHIMrqjDIlS80hDwb2X38jUDpz978"
    "+mZmFN8KIqSSgayDDlHj8KQc/RX16RQCZvvJ1e4VWS1Jwv0bJLOQyzu8vgY5MUQZBYgq8Tfw4Zdliud4juEiGMgJ9xQReEYiIH5t7zV9zTeW"
    "cjp6/T9ZOIGxu7iy+VjSrgALIIxEiBQI971rlix/x7Ev0bUE/91/s/Xp64pAO0Qmgd/gGEGsq3uXcuL7K4Gh2L1t2BGweElZ+eLieQbs7wtg"
    "gbsbawFhvQuAKyD31XAkAXrgHSMgenk/Q3mNoJkYCOAZYFyk9cmX9igqeUtkUMzC5xfP7+4mU7xzZo4QFOYX2amAFHt8eAe74r+v8RBBaKBa"
    "taJAx/ExUE3MkwJto358odJ1UF7FEnBYKovH2zoMKAQRc/2bOWSXoUg9jIXX7BNpC04dXNLnPKVw8efBBIML6Li22q/ae6+CbRlxEODfB4HC"
    "AqR0+Nk4ONsNMA30jNIzwTxCYstsomvxSlmmIssvwOdJ8rwZjgYh1kTnr1/GAGKqX0syU3j8odEEcalGwhn4eamyLet0KJyggEvNWjrNVtfz"
    "hi5OAA9RWmPJGH9EVzfUJ8Mf6WVI18cqeykTYZvxmlnrAMRsDP2B+yWjunhqIRVSTQHhc/d/TSp43FtRfDZzieGvyE1BcGyAPmh+wZjtofNw"
    "ZweurJwAA7BlPi8lHqKeNzCLOKB2K1pLYTvY7snua+D/NSxw1BBis1AguKmUkRGtGu/QGnmY+qJOFKfeZ1WqaCw3fQK1FaBJJkQZfKRNci+K"
    "Gk+EJ0dK3gkq4qHvIK2XxGniONRRZYFsIWYmBUSQD4a3SBARBpKSynIkWD0qlL2LVLVtLk1iFd8G9QsRX9S9wfYvIVbdliChKtm/foBqUCGI"
    "8dzzvhomQfcB7AT6wDpHMj8TdtmE/ePWERRYbcp9lattfIAqGPDPs7o4Ibprj7F5PTlRUCl16oabCdQbc7wAgEW1+kME5j+xEpG8gXjM/E/i"
    "f1hNC/NssCYsIIgBNj3/UdWAEL+LSuEF3O4qFqhg8RU+B5U7mk1EI65MROXaQQW7JeoFZh6dEQsrtagAnx6drEAxmA6MRzALWJROF3xRFBqV"
    "JrvFXhZ2QqpQIjZNgIXLCTehrQEggCsBAC9IdEl+CPsSik9M7vC8sD4VgYVqmusqIKrsDULYaOd4ZNeVCt/VYWm6LgX+Jguky0APZK7pPSor"
    "P/7xU0WLPaW8odLYCSxT3EMi777CV3iJnIdynURUO3ViTHWFm3id/HeIKgIYaeG8wR6si1b91aj3jsB0m0cO45BYqRC/3IrwYiOImYRluHAX"
    "abimrC4VhGPwl1NQxEH0qB1pbgLcrSrRx0CoM1B727KETr1GClyy2wCFaun69GJpRHs1OX5X52g/pN0dfVWrJ11WJ0OTQ0le6ho7NGXFWwkB"
    "N7rBghAtekh29GIIk75AdYoIT98so09PetNp7x4EthJektVNdtJoYumPlc0nbInFJuRKx5kzfjWQFiwRmLouAIuu2DRuxrlugqCDThmYJyYr"
    "d1qdChbCBEEW/KjwldtAqIKMGG5IFIZ6VkiMJlM86WhgWo5CpT86RcAKFqH6G+0LLP1wrwjVw7AstZnDCtSf6oOMzjGH6LGoyJf4wsvaVMRQ"
    "yOiADTbIJijVPF2hyt6V3UtkoTUY9aW4RJY4bjJ6Q5wIqgDQNKJxah1Mvd3GPp7AU47Qqll1NBZtE/paqL7WSuAnS26tE2T0zVWDDOm9LCTG"
    "rh1QslSmAezmoxBbwNDWbde5dwr9wBa3hkZWcVMaWMWOBWYhtUhjoBaqq+8oLNfrIMluWJLd3cXo4azPQmoAyqvhbf2ifVxkBZV2fwSwQQL4"
    "eoqldVDUN70ortdFKKPWz3ElvzAZnoph6tjifgJcUY9LpFD2dhULBp40fpOaCIoCrNPjzmFK4qSw3Rp7o4B8fWR54fziXbPRQVEVqFzj9Ijc"
    "EZ0Qrcgt4seNs+PmBbthcAocZPh3UNCt4ZNOXa+ESL7yfEjg/W7Gym8pq0cozVJgeTU8rxne1sMYnKYqvbSs3xce1/Pq8c/sU3EcriVpBFKy"
    "/ng+GknTDyZjhYkpRHz7YNKnlYep64oOwCN4cMjj/Us85FVYcJDh9zocvBAUxNf47bLxttiAvENFgOCuQSRAJqFiTLokWJz1+gBix7ovBg58"
    "96HAsL7/iKCw1uoDhDdXYBFoqAkeCpLkSh4RLslV+4DjrXm2CHDUBA8FTnIljwgcz6odwDh1DxcBifNqbvyKBxjmFKlgMGZcEgxO+UQHM4Qw"
    "tTxmuNLY0pjhruRRMSOxajTysxcCPPt3c4xmiQB7qIyRSGrhgyKFDDUtGc4ltzLESjTKQEaG+egv9o6WzS5LZZq/bNScIxWv4p+QFyMCdfxD"
    "OLojzfYHBr8p+ttpovh3uaSQXI6fxMeNWBySUbTwA/Jo+yPJlmxN+U14raCEOBbFhzCoZn1LRMHlAEgiwWqhpGfNBpUe963Ai0vJrhhcatJs"
    "aKlhzxRY7OviXE52LMqCFIp6uXCzl66W6plJjqq4U+MuK853QqOxvAXTcllPXRYzlfnlcv69daKhKrvBdqNWCt597NY7pUCFOUINYyhhvOOC"
    "WEESNB8wX9Vl9mgDVZ6uMB46k4Sti24HsmX1+SwKevbbPjLc6SPLAP2fCHHwXcM8jwZyXeyFvrMUqqsl/mOAvwpww/+PYwxGSIIySdaTwBOR"
    "XvKpHxic8l/FChMSLp49f6ISpcPbEH0ZV70+O4MsoRHtW0LCwshVqBxgSKX5Yq0ZCa0FLnvSpEFrq7j6gAZwr5XD+YayU+j4kDDHyuKzgZDb"
    "hECmA3LZZCPjPIWXKJzHytehJ5dwTuofxgLY5BdOr/oUTA6F1zVaSQtXCMFVcQVyC/4TgU321XRP9dKwAoXBt4gnzxY+MvJSi2i7grbI8jbP"
    "NsQwkvAcDZdkxzLyDSQ6e5YplpO7SCr++6Tg2g8xDUG79FYJt/2Vwy2x2scGoIwmkoG7dnGSVcBJlSSpYlwIGFa7C0EsfYGPDZqcfAdyR/z/"
    "7V1rTyNJsv0rKXSlBV0bu6qMwWa3JaDpbjQMzMWwj2mxlrENWMNjFuOZHa36v984EZGvqrLLbtNfVj1f6LHLWZGvyMiIEydeJr9SlO3NxirI"
    "P1hpjFQuGqWi0IGYXzNipU4h/6Sg4Z8ZfzR4uMOivn+U6htco1oAVafn5z9YELbw+mq4WoKu8oXwJXFhdAvXPhWiCn1YWtmIotklo+FxBfGj"
    "XGIT0XeSqDgP/mhaNAnPKJrAeI9pwIOCztOo3kxGdFvIi0RT8iAwzddnQYq4tVVcYoiFzTiVoC/oOzs3Cunp42SSkCSgBn392OUV+DwSDU/J"
    "+DPagJMesA4RxnApLxZ/oGgtjtroeAfVMKRhWl+cDNxfcrXjRQWjzadVbRTaXXPocq29jP81mwTwiyjLxsJuHC2O0JsT/gyJIRyTZMK6RQtM"
    "HTMaa6evfO/ZpSWvJxje6/Be48jdROAYwfi5qQgSzhaMKYxcgmMJOMiv1a9d0W+hVq5rLoutbwOv/wHy9IWS/0YKXc3Agept3qk5MJtsXxlo"
    "c8bsMzDWWJVSM1YN1WE1c8rl5Gn4MGM+QSZMtWrImoLuFwa/2GIY7KHZ1D5a4LG909cMRtYiwiWWvBVpN0ID/cHgqlxIkIK8x0c/YPccMGr0"
    "IzFF9wTTGQQhf6TgtqIbAoU5Y0DuqASt7R9ix0ofsXT35XjwQgBwSX8LoMOf57oz/dQWXSZSh4v7XYAdl1m9YQA4WANO+RcvF96mdh4Ui0QN"
    "DfNpaVyUlrJYRCLZNNxMtlO+NfsiZJKoRyvKY6R73AvlUvTTZtrsJyk9MoDYjCyz9wsLM9fBDi9nfUsD7W4Hmk4xp9nuxv3r66/TbqOBUdb7"
    "8fbzy12Dn2/geUo1aDh3BaXY3k1uJg/BGCGdU8Pknz9bLAPhnY5wHJLgnzdiPmFgoi2t08b1dTzC36PM36PM5VHm68JGw1rJHSPuACfc7s+w"
    "ynBfhMWq5UDsQeL2OWt9yfiWbFZSK9ROqzVqjnfTVnPY2R0Nh0naamc3O+0kGewORrftJOt0OmlrtBvknfRB0IksqmeCYsYdSxu5Hm1jt6kT"
    "IlAQ9Ouyq7N1pTB25B/9hX3kcjknOGBhQcbUhIsS4NPVY+9YotXDn33N8I9vRqNhpz1qj26y3U52M8iSpDPevRmOhlSUIU2T29bNINm7XW74"
    "s68Z/pKrePU8ZGvPw9cREVwvPiUBlKP8LDprKeMCMDdr/Z1dse1cgLiRk5VIjp/U44hziuqcqk24IZcetdh7RycnVJTiI0EkBWj7t4uTy0tc"
    "kHgIzn+CIUdj1Dv5eBZAkajIG//9+fjivLdPGDKMGeGiCIyGRAR8LK32QmkeiUR08joTML/FnaFlwKaIEyJperCxk+PvPxF837Yev+pE3kTA"
    "Om6FOeXZYKXT6fTkZ8cvTwjSkx8ZZIawUO/TyQfGAQ7+PXmcPeLug1zOMSdPPZJ7x8pLTKP8n3+0bFxpelrNTts/hIr1fCg8FZ4IkId2MZ5f"
    "0DBhhMMJZeoHi+Kjz7hcY9QtLOf8eypnmPxHdlhx2foIaxLpMViVQml4cdkrmWWu93Wh6D+e8vCAKdhcZCdGweR8uPS62oxid7GzTpxr3Jsp"
    "gvOsKaMFX2x+JOgbDROPo25jnDqfNzRHsy+M9HLu+R+qEQBYqnab7kgfMGJUrFUa8L6G8IVS6lOesLFNpDm+wktID/zzc7PeGdRvr//Tbn35"
    "H3oO/fZVL4ezF0788SYSvrpjI/1LlQ383QHy3QHy3QGypANk3tV0oSnrIBFzw5DdZNFVEcatFIeWjeDyLHM+kFUDHGGbKF7G5fGWaVO1YEm7"
    "DasgQcHUbhVes47opTGGt+xD/gVVnbEKqeR1i73/X9mIFXmlUV3eGeaoqJGk8DSki707QJmMou+z8m0iNlkjO6Cd+Te1bll2HJ0Ffojs9xSX"
    "dxE9JOmwjZlNfmhr34SMI3U2iwxS2IzQ2kwNMuBt5nuGoAh/jiwi/qbGfzJ2nuGR5kbQoxLJmbXM+iNgl0c0Bo5BR7uxw92AQqjTZFJJTiUm"
    "MExMQKQAhtkVWIgkFVna/CfbFZl3smVakJ82W9JQU/7I/6XyXSYfZhn/aUm/iQoAvR0/wnNJeTgUOnZ0LZbYivuRNjk4Yt1tRjQ1TQjes2c2"
    "2Zg0SbplJOIiY+s+z7ZqlkpDZBbPnqOx4WA3qWiCHnhby3GG4R1tJTNI2gcyLkn7EHaccDPId0zSwH8PJYMMGiahBm/F7eCXGLCP94Mntn9j"
    "Bn4wf348PT9kDouT/7s65sRK77S+Ig77I8C8LAW/2eT7mS+wRguLC6zp4WRGM+oZWFFA10HjICUnhUzUODo0wC9uxaH2PnEUGMrq0eJNSqko"
    "T44e4VCAHbYTAegMvPo4+0V80zDBd0wZrhUAmQxa804hv1CEKN2p48LYDLeXfdxVZa1xXS/eO3Ik7Yf0NbJ57cBsRX1Mc33kucv18Sjuo9MC"
    "dev1CpgzrC+24UjXHe0SVcKFGeXo2G9RFYVNKtMEp+a7ZN+w5UvfuaIBbAGKdbpvgmrEQs3GTnbx39sZ3CJiRCpP8USDx8yIHhDof+TFhat9"
    "Kxgsz8PSCCg/KJex4L80jXLACHWSRobTJ423gpn77HlG2hAaRLptNiVA8dOn9/Um1AH+tuLpyXLTk3RKpqdmCM30MZ6koMQWKDNCurqueX9B"
    "V3znQkYsWDBNPCX6T9okxHm0VK0I/hmb6PyrqAOt/PpS9Sd6L0uL3TmY2xFX1MRx5biDuax0GIRR1iavVrBFeK+4xnwb9JuaL3QcMovtg4cm"
    "4OhB66Sg6Ib3MrmZQbtQNSk0JkpTKk/5mH/4DqIKCuc9jed7Jz9ceyUDRJi1eIxoX7y/OkICrMyNLy61kpSQjZZ6HnnLefIhyIy9Fjwu+Hg0"
    "GwI9FlZs8/1p5/vTKe3P+7g/xBlC54rW47KkZGTu1/UTTGKwt8CYpArmYXAzfuDvyfyk//td5tky4pEpdUdm6Xbcw74sHg0QhrOTxLOzm+sN"
    "M/nkevOhZmhDfoo7JJfKBjQDxXX+NeMzyNTfGXVoCjeiqEe7VKEMJUjzUHi88Wf6QPgo3zWUz532YCNX71HLjsrPI+yy7dFeQf0fFrtE2iV3"
    "BBTphLbnBATNJk/feATDA4tsCIco9Keez/K7ug1QGrcaBd8dT0AnJ24zi+ytkvP5Q+7skgrTzvw2v9HauZnRbvhDRkuEVKdYQ7xwphD2CmyE"
    "Zl5D7xSFmK+baXsKUeEMbArMmiQv2XZ31H3RRIFhQ2x4rHIHxi4me1Dx6YJ9zapvTAFDXlOxxAWzJi2d8pyOEX+sxb5Kbq87yqFl1HnaNfMo"
    "YcQ7IP2iFYxY+Tvzv4azh5lRj7jm3F6ORc5bKa1mpZUSUxNsW7UujDSeeYY0+8imnlODwps3pRH99WFAq/dPv48fHupgdxmP/gQ7ge9gdo1O"
    "tzVkzh9vC5ltzk0R9CJ/mLfKlgorL65sMyPSIxpb+h1QCs+307iD4tCz5q8QOknG9fFpD87i01OzKZQNqjZ1Nmpq9NbYUmHiw3iXJflDW29E"
    "SaZXF5ZRmrarsv78Umf1FdFs5joniGDcBtK+pSvDjuS0caZ3xO4swz3nFHhjgQLf1z2MiW7I84Z8M8zRju+wxSavOB/EXJs9/fJEM8fYjeA2"
    "hynAR/XpOLj4csgLg8Kng1Y48kLziW3s4duNbIjQWKedj9VX85aMbItaYCn4c8Af592lDIxIyLRMyKRTZfL6C8kqxm9gj0eYGFMaH9+KBM3m"
    "CEr2/qn6hZk3AR6XrikCBAOZpjVnD4Z2Ait8/j2NM1OZBwcB837AeA9N9EjAVqmATWPjBm4rOu0opyC7PhK6hMfKk+rRXSGwxt4fuh5iP9Mf"
    "f1+Z1248bDulUu0aB4C1gUzY7kcHF+8RY6LWurJNHv7gKqju4LC3xfwyape9hjwLykubI68NPEVuEJSo1pPamqC0V/iq3bJXtZqOLnj0/Eje"
    "f5w52KPeJPrlnaudboSpI253z2mfnVxg1SshdpYxnyH+fZYEdIhwbhBNhAE+yjDvh8EpBN+UYYI6AwpDOk6IRBVHrOhHcKqE+DHL4wTxHVET"
    "lC/a+/NfTLuFb/gs3DftHfyPHo2WaMOoY8gOQHx+6vvCcqNUrZFtsH3hHtUjW9Qd8/Qwqxqnargh/2x5MoqWXqOMNbJWTvLYAPdLwIES8740"
    "gjDoxnVMT7rwh/lzFDtz4yzNTRbpr1dmiIWfh8flLxZ1R7YnrX3QVwbqQSmqzO/3NAxqdAW8s9gZtO5oPqAWBvq4DviUjkMyb5hzl97Hhq2E"
    "9USRkDFPRn6hTfzuSYoPD/RJsoiESPNhfPvqP63zmpJ/0zLJ0mCZaO+8BDOWDOe0dNL2LFpMbGNIH3gVDEn3v45lTWXZC44ksqFsBR4SnyK0"
    "BsY7P8Hzvm/WW5HrLbpGCb3YonXIpPYHgEj6A4Uiu1I0d7kVuUQT5WszY0Ku8f3gtwm4iawNpyyLEteD82L8qqT5ls7MuLgS02FMSLnAIFHD"
    "zvlo+YaiTk38XPiscJIjbRf2K+JWUKF4RdwxOYe49mWP6lRLPPgSxPTqg5OymO9788zXyfOMmF4pTsbJvvbFJnyxsGaT8HpjYQMSRpl1SVjD"
    "wnbX/YKJd6ymDEx0LBdMia2r0WNiLh9ODuaDH/OcgxXPWQq8hY8tUk3LLhRGguKYwuROpr9IqJC8l7Q/7NwI0vf4jJAhx8cXFoLRI9KoCzb6"
    "zy9+2P/ximUm04iD+rzoFrCe9S1AIj+fWTuidx7f6n1AF+nzDUxuW6TDM4PTPLPZSWTSZEyMnmc091N4awxOSznpRSHB204TTzTjllj8+aWr"
    "R2mLLpDwjza3m20zremne/ppst30Hyapfpo2t3fN1InGtwGFfeMGgzFV7mqCIhFJnB+U479/OqBRY57Jk94PEXPXMbM1gafLs0eVZqQ4WykY"
    "i8EdjohX9VK6yvI0zzOCvPw2DpX/3cvg8XGgsbtcIAYrgQ0mC460cS+hAU+weILyGwifRpU34mosiSD84jay1dpIy9pIV2sjgwG2Trp+rhJL"
    "EzItGKbWGwxTe9Vhuv42+cO5ricVXd9ZteuR2Kz46eWkvC4CeQXGIuxmjv/MfV2ok1Mh4u4aIipyMzekFwd/swOokDkCsvWYDviqVxjCrEK+"
    "vTeX70Sol+Pwy/uTg1OJ/0fStSqk66w1wQwa8kFUvw0FfCjk0sw5J3dV8sjv5SXcWSwheUbX3n1Jur6SSrJVlVRJGysq3FZJG9mKcuxE68lW"
    "ryrVi1rACmSAV95xkJ+vdsV8tdZaUSuTA+Sk262Qbh2FVhy9EgmZvVq1WtAX3bqsqvMy71XITBiJtVXIkkkCkVydKrkOv4lcWZVcScWBney+"
    "oVzOAQZAOUv0Vw7/54UszGpScbYme2+g2DprmBVC+nmM1PZAcx9cXX4651sBw2d7cTannocOHF1yHiYVB3aart/vNFmj3wAj/MN2yHHT6gal"
    "C+sHCnmEFB9x7yqO+zRbY+25YY1qfTm1g4ki92txpVUc8uk6KrmInnLySHE8e8WJJKo41NMdgXaliopL2TyeX6LPwtZ2uEKk/AD1waUJnNf5"
    "7oXVALt+koMiAUsoAfc7DuTyphDycJ6Y4jxUHI0MZFtjccC+o6gcpV4cnobGlizlojgVZyFXJGIQjf5Nl5oE+plOAv2wm9qfwuBZOAlOcCzh"
    "/spTorGrJbpdcZxm6+wGcXKpzDacJkTJF1c2lT0Wp+IUzXbWV4cWXJott43oMTtvu9zgG89bmfmc7a1vPrfewnzurGo+l8ix4pWkXWpEFhYy"
    "WxLRAiOly2UwClfiCtOi9QZrqtVa/87Uar/BpO+tP+mt3TXuTN+g8O+XfBlfzceQEiPKM2Qre/qyuZoNhGK0yKev5Jrvzn2mnCcf5S84X+3k"
    "8rjy9dFCdSU1uI6GTZAvcMtLXYEmjKxsQdNO45xhFB1kdJ7yWaKh9X69lgjeH1n1qN6AtOHwnobISc+O6rzHsv5fkbji3fL6fNGA87N1rFGF"
    "UjvPf1tzSY2HVIAIhimVPD4m1Pnx2RJDEMCtjzSDdvEPFle6jb6VGhG2siE/Itk/C+rowoLuVj0QtLDkTKM63gWsgZMzcp981ePiPMjBcBe1"
    "oeVBbLUyeeOiUnmLi4XrilHVqGaA+1T0oK9cFQSlpEB2VZeRmnXEmQzhvFKxvDP7Dlv5imuDnXEBS9uoe37uM19ySnWOPh1wHRZE9BewYHbn"
    "J29JqeElFbDHEiF2HZZH3g+wR3kcC0MsnoIywvkfh4WONUNHkVY1DpRP50TKBZzKmEbkeKBKE550hZpdUSZ8Ja/iGCsXZ6z7oFMddEaamYgG"
    "FGmNZFwgk18NlU/Xn296UAuhO6f+XQSOK8H/lgTot+YdTWH5ZI2lyTt59KTodPzF5nRsC8k7MDeqJcmC2ao61tasIK5fMiBio/p4DJic8pxG"
    "WIMTojyhOOd2hgmQRBFblH7lA9QBxAHlDDI3uGm3XxzKXIttU+3kpydOB6A0+Hu7unI/ByzMobpkBOoyGb/S+jabnxgcv9xJ7cTcFDIh43iD"
    "tirFXfVAd+9aczhKRnTJISlaDgUAZU2WepENqNKW2IAQ9lq4ilGR++GS1sWCjXP38HxDOlgQHVBhDZ/pvZzhEQA/ygekzyk5hUIwNVNeCKVm"
    "ymGpNZPnDcaTc2pCzLV6LMqJEUYqbzgglQbQgrGMSmh5GMAS5pBHGgAPpPxMZlNxmVsqp1vyxd3Am8D+gNOR5u2seTvIpnI4bHWwnucYV76p"
    "haT/TgOsYnTl2+Aue9x0eSbTdkkmUy0/SnMtN05tUAw36QE9Vd1Z2nU4b6V8q5lSrjc7WxhMB2XltnPTyGBXxbhiNt3D9iCpMBd51SjPt9sy"
    "PlVWTviFzHt5UzOnXZa3OcXRRdggZxiFwx7AM3WdOsFqAaDeGVxbFdbqoj2IrIjhq2exoUHFp6S7+6FiW2DqzjcaawttQmta1W1eL6uD+vNQ"
    "MKRDTNJYDaG4A1ZjeNaDO1LF1A+nS7TJhtqO9A+xmFBk8PmVsyKEscthsckdnkg6yBMgS31N4KdwJ+jkLTCxz6me3SY+U2sciUnkx7EF6h2k"
    "6vL8Upk5yhkIrPBMqT4haiiyesEQQTGbTk2KlIqfhYCT4+EvQPd2dhNf8T54ggWyn9/PqF0mc5pKx4LvQiBhE6JFePAABjplV6I4gqbslg2k"
    "TxHA0BH2WUHoR8CqqoE5pWtCMeQ4i0hrTxYUYZRp1IirlMrXG/7lI27DM0LErNF2FUg5zp9Ue3kL9ttKhYLweQKbUCIbgaed9IEsvU+XgsPn"
    "8i7kB5S7jU0oiikySumjSxi2Xe3lkI/U5ogAzs3pILJGp5J95hYiXJBeBgvPBcpPz70A6HdDe4zyAZCdx0houbEw11HtG46wuxC78aG2yQ6+"
    "fw3HuUcmxJkwpsmWZwamBVkpG7VgGoL6HNZKe+Z6FVHq74Tvg8Nw4K0mYva7aGBrOdIHgcS+1SB9qeVcwLr9bL/z37E3SgHcgcQlT/4XjEtw"
    "ROJoPul9c92kxyufqn2c66yVw/UpkCbxx3+1LGFGJhpV0Iezafny/m17+hsbSf5eIV4A19EvX/4fYi7OkQ=="
)
_REGISTRATION_BLOB = (
    "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"
    "BDLjRqZEPEeUNx8+/D/JlSR/"
)

MODEL = _load_commitment(_MODEL_BLOB, PROTOCOL_DIGESTS["pre_execution_failure_model"], "model")
REGISTRATION = _load_commitment(_REGISTRATION_BLOB, PROTOCOL_DIGESTS["registration"], "registration")
PC = MODEL["protocol_constants"]
DV = MODEL["derivation_vocabulary"]
CLOSED = MODEL["closed_vocabularies"]
FAMILIES: dict[str, dict[str, Any]] = {row["family_id"]: row for row in MODEL["families"]}
STAGE_BY_INDEX: dict[int, dict[str, Any]] = {row["stage_index"]: row for row in MODEL["stage_ordering"]}
BOOTSTRAP_ORDER: list[str] = list(REGISTRATION["stage_order"])
ENTRYPOINTS: list[dict[str, Any]] = list(PC["entrypoints"])
BOOTSTRAP_OBJECTS: dict[str, dict[str, Any]] = {row["argument"]: row for row in PC["bootstrap_objects"]}
ENTRYPOINT_CLI_DEST = {"candidate_package": "package", "object_registry": "object_registry"}
_NUMBER_LIMITS = PC["json_number_resource_limits"]
_HEX_DIGEST_PATTERN = DV["expected"]["LOWERCASE_SHA256_HEX_FORMAT"]["constant_value"]
_HEX_DIGEST = re.compile(_HEX_DIGEST_PATTERN.replace("$", r"\Z"))
PROFILE_SCHEMA_ID = PC["profile_schema_identity"]
DRAFT_2020_12 = PC["draft_2020_12_dialect"]

# The registered preflight branches of schema/metacontract.schema.json $defs/pre_execution_result fix the
# `operation` constant per code (model.witness_contracts.PROFILE_PREFLIGHT.operation: "the const of the
# registered branch for the family code"). The model delegates the value to the registered schema, which is
# not reachable before the registry is validated, so the registered branch table is carried here.
REGISTERED_PREFLIGHT_OPERATIONS = {
    "MISSING_EXTERNAL_PROFILE_SCHEMA": "READ_PROFILE_SCHEMA_ID_BYTES_AND_EXPECTED_DIGEST",
    "EXTERNAL_PROFILE_SCHEMA_DIGEST_INVALID": "VALIDATE_EXPECTED_PROFILE_SCHEMA_SHA256_FORMAT",
    "INVALID_EXTERNAL_PROFILE_SCHEMA": "VALIDATE_PROFILE_SCHEMA_ID_DIALECT_AND_DRAFT",
    "EXTERNAL_PROFILE_SCHEMA_DIGEST_MISMATCH": "VERIFY_PROFILE_SCHEMA_RAW_SHA256",
    "MISSING_EXTERNAL_ACCEPTANCE_PROFILE": "READ_PROFILE",
    "INVALID_EXTERNAL_ACCEPTANCE_PROFILE": "VALIDATE_PROFILE_SCHEMA",
    "EXTERNAL_FROZEN_R5R2_CONTENT_MISMATCH": "VERIFY_FROZEN_R5R2_CONTENT",
    "EXTERNAL_FROZEN_R5R3_CONTENT_MISMATCH": "VERIFY_FROZEN_R5R3_CONTENT",
    "EXTERNAL_ACCEPTED_BASE_CONTENT_MISMATCH": "VERIFY_ACCEPTED_BASE_CONTENT",
    "EXTERNAL_ACCEPTED_VECTOR_CONTENT_MISMATCH": "VERIFY_ACCEPTED_VECTOR_CONTENT",
    "METACONTRACT_R5R2_PIN_CLAIM_MISMATCH": "COMPARE_R5R2_PIN_CLAIM",
    "METACONTRACT_R5R3_PIN_CLAIM_MISMATCH": "COMPARE_R5R3_PIN_CLAIM",
    "METACONTRACT_ACCEPTED_ALLOWLIST_CLAIM_MISMATCH": "COMPARE_ACCEPTED_ALLOWLIST_CLAIM",
    "METACONTRACT_PROJECTION_CLAIM_MISMATCH": "COMPARE_METACONTRACT_PROJECTION_CLAIM",
    "PROCEDURE_PROJECTION_CLAIM_MISMATCH": "COMPARE_PROCEDURE_PROJECTION_CLAIMS",
}



@dataclass(frozen=True)
class ResolvedObject:
    ref: dict[str, str]
    registration: dict[str, Any]
    content: Any
    raw_bytes: bytes
    canonical_path: str
    source_universe: str
    requested_ref: dict[str, str] | None = None

    def public_record(self) -> dict[str, Any]:
        mode = self.registration["integrity"]["mode"]
        integrity_source = {
            "SEMANTIC_JSON_CONTENT": "VALIDATED_REGISTRY_ENTRY",
            "SELF_DIGEST": "PACKAGE_SELF_DIGEST",
            "PACKAGE_PINNED_BOOTSTRAP": "PACKAGE_REGISTRY_SEMANTIC_PIN",
            "DUAL_ACCEPTED_SOURCE": "EXTERNAL_ACCEPTANCE_PROFILE",
        }[mode]
        return {
            "kind": self.ref["kind"],
            "id": self.ref["id"],
            "version": self.ref["version"],
            "ref": dict(self.requested_ref or self.ref),
            "reference": dict(self.ref),
            "path": self.canonical_path,
            "status": self.registration["status"],
            "classification": self.registration["classification"],
            "roles": list(self.registration["roles"]),
            "schema_ref": self.registration.get("schema_ref"),
            "content": self.content,
            "origin": self.source_universe,
            "integrity": self.registration["integrity"],
            "integrity_source": integrity_source,
            "members": list(self.registration.get("members", [])),
            "raw_content_base64": base64.b64encode(self.raw_bytes).decode("ascii"),
        }

class TypedVerificationUniverse(dict):
    """Verified universe value; its public JSON shape remains {objects: [...]} ."""

class TypedResolvedJSON(dict):
    """Exact public JSON record with RESOLVED_OBJECT provenance from an AST producer."""

def erase_resolved_type(value: Any) -> Any:
    if isinstance(value, ResolvedObject):
        value = value.public_record()
    if isinstance(value, TypedResolvedJSON):
        return dict(value)
    if isinstance(value, list):
        if any(isinstance(item, (TypedResolvedJSON, ResolvedObject)) for item in value):
            return [erase_resolved_type(item) for item in value]
        return value
    return value



_ABSENT = object()


class Decoded:
    """Result of strict decoding: .condition is None on success, otherwise UTF8, SYNTAX, NUMBER_LIMIT or DUPLICATE."""

    __slots__ = ("value", "condition")

    def __init__(self, value: Any = None, condition: str | None = None):
        self.value = value
        self.condition = condition


def _decode_nested_json(text: str, members: Any, number_token: Any, reject_constant: Any) -> Any:
    """json.loads(text, object_pairs_hook=members, parse_int=number_token, parse_float=number_token,
    parse_constant=reject_constant) for a document whose nesting exceeds what the C scanner's recursion allowance can
    follow, on an explicit stack: the same grammar (RFC 8259 text, strict strings, ASCII-only number grammar, only the
    four JSON whitespace characters, no BOM, no trailing comma, no extra data) and the same hook calls; ValueError for
    malformed text. Work is proportional to the text length."""
    scanstring = json.decoder.scanstring
    match_number = json.scanner.NUMBER_RE.match
    size = len(text)
    if text.startswith("\ufeff"):
        raise ValueError("BOM")

    def skip(at: int) -> int:
        while at < size and text[at] in " \t\n\r":
            at += 1
        return at

    def member_key(at: int) -> tuple[str, int]:
        """Property name and the position after its ':' separator (and the whitespace that follows)."""
        if at >= size or text[at] != '"':
            raise ValueError("Expecting property name enclosed in double quotes")
        name, at = scanstring(text, at + 1, True)
        at = skip(at)
        if at >= size or text[at] != ":":
            raise ValueError("Expecting ':' delimiter")
        return name, skip(at + 1)

    frames: list[list[Any]] = []  # [is_object, items (array elements or (name, value) pairs), pending property name]
    at = skip(0)
    while True:
        if at >= size:
            raise ValueError("Expecting value")
        char = text[at]
        if char == "{":
            at = skip(at + 1)
            if at < size and text[at] == "}":
                value, at = members([]), at + 1
            else:
                name, at = member_key(at)
                frames.append([True, [], name])
                continue
        elif char == "[":
            at = skip(at + 1)
            if at < size and text[at] == "]":
                value, at = [], at + 1
            else:
                frames.append([False, [], None])
                continue
        elif char == '"':
            value, at = scanstring(text, at + 1, True)
        elif text.startswith("null", at):
            value, at = None, at + 4
        elif text.startswith("true", at):
            value, at = True, at + 4
        elif text.startswith("false", at):
            value, at = False, at + 5
        elif text.startswith("NaN", at):
            value, at = reject_constant("NaN"), at + 3
        elif text.startswith("Infinity", at):
            value, at = reject_constant("Infinity"), at + 8
        elif text.startswith("-Infinity", at):
            value, at = reject_constant("-Infinity"), at + 9
        else:
            found = match_number(text, at)
            if found is None:
                raise ValueError("Expecting value")
            value, at = number_token(found.group(0)), found.end()
        # `value` is a complete value: attach it to the open containers, closing every one it completes
        while True:
            if not frames:
                if skip(at) != size:
                    raise ValueError("Extra data")
                return value
            frame = frames[-1]
            at = skip(at)
            if at >= size:
                raise ValueError("Expecting delimiter")
            if frame[0]:
                frame[1].append((frame[2], value))
                if text[at] == ",":
                    frame[2], at = member_key(skip(at + 1))
                    break
                if text[at] == "}":
                    value, at = members(frame[1]), at + 1
                    frames.pop()
                    continue
            else:
                frame[1].append(value)
                if text[at] == ",":
                    at = skip(at + 1)
                    break
                if text[at] == "]":
                    value, at = frame[1], at + 1
                    frames.pop()
                    continue
            raise ValueError("Expecting delimiter")


def strict_decode(raw: bytes) -> Decoded:
    """Strict UTF-8 JSON with number resource limits and duplicate member names, each condition reported separately.

    The four conditions are independent properties of the bytes; the caller applies the declared rank order
    (UTF8, SYNTAX, NUMBER_LIMIT, DUPLICATE), so the first condition by rank is reported even when a later one
    occurs earlier in the text.
    """
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return Decoded(None, "UTF8")
    flags = {"number": False, "duplicate": False}
    max_digits = int(_NUMBER_LIMITS["maximum_significand_digits"])
    max_exp_digits = int(_NUMBER_LIMITS["maximum_exponent_field_digits"])
    max_exp = int(_NUMBER_LIMITS["maximum_absolute_decimal_exponent"])

    def members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                flags["duplicate"] = True
            result[key] = value
        return result

    def number_token(token: str) -> int | Decimal:
        lower = token.lower()
        mantissa = lower.split("e", 1)[0]
        exceeded = len(mantissa.replace("-", "").replace(".", "")) > max_digits
        if "e" in lower:
            digits = lower.split("e", 1)[1].lstrip("+-")
            magnitude = digits.lstrip("0") or "0"
            if len(digits) > max_exp_digits or len(magnitude) > len(str(max_exp)) or int(magnitude) > max_exp:
                exceeded = True
        if exceeded:
            flags["number"] = True
            return 0
        if "." in mantissa or "e" in lower:
            return Decimal(token)
        sign = -1 if token.startswith("-") else 1
        value = 0
        for digit in token.lstrip("-"):
            value = value * 10 + ord(digit) - ord("0")
        return sign * value

    def reject_constant(_: str) -> Any:
        raise ValueError("NONFINITE_NUMBER")

    try:
        try:
            value = json.loads(text, object_pairs_hook=members, parse_int=number_token, parse_float=number_token,
                               parse_constant=reject_constant)
        except RecursionError:  # nesting beyond the C scanner's allowance is a property of the scanner, not of the text
            value = _decode_nested_json(text, members, number_token, reject_constant)
    except (json.JSONDecodeError, ValueError, RecursionError):
        return Decoded(None, "SYNTAX")
    if flags["number"]:
        return Decoded(value, "NUMBER_LIMIT")
    if flags["duplicate"]:
        return Decoded(value, "DUPLICATE")
    return Decoded(value, None)


def parse_json(raw: bytes, label: str = "") -> Any:
    decoded = strict_decode(raw)
    if decoded.condition is not None:
        raise StrictDecodeError(decoded.condition)
    return decoded.value


def lookup(value: Any, tokens: Sequence[str]) -> Any:
    """RFC6901 traversal over a decoded value; _ABSENT when any step is missing."""
    node = value
    for token in tokens:
        if isinstance(node, ResolvedObject):
            node = node.public_record()
        if isinstance(node, dict):
            if token not in node:
                return _ABSENT
            node = node[token]
        elif isinstance(node, list):
            if not token.isascii() or not token.isdigit() or (len(token) > 1 and token[0] == "0") or int(token) >= len(node):
                return _ABSENT
            node = node[int(token)]
        else:
            return _ABSENT
    return node


def ptr_lookup(value: Any, pointer: str) -> Any:
    try:
        return lookup(value, pointer_tokens(pointer))
    except ExpressionError:
        return _ABSENT


def pointer_of(tokens: Iterable[Any]) -> str:
    return "".join("/" + encode_pointer_token(str(token)) for token in tokens)


def utf16_key(text: str) -> bytes:
    return text.encode("utf-16-be", errors="surrogatepass")


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def typed_identity(source: Any, members: Sequence[str] = ("kind", "id", "version")) -> dict[str, str] | None:
    """TYPED_IDENTITY_WHEN_VALID_ELSE_NULL: every member present, a JSON string and non-empty, else null (D14)."""
    if not isinstance(source, Mapping) or not all(nonempty(source.get(member)) for member in members):
        return None
    return {member: source[member] for member in members}


def is_decimal_integral(value: Any) -> bool:
    if isinstance(value, int):
        return True
    sign, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):
        return False
    if exponent >= 0:
        return True
    places = -exponent
    tail = digits[-places:] if places < len(digits) else digits
    return not any(tail)


def json_type_token(value: Any) -> str:
    """closed_vocabularies.json_type classification of a present value (ABSENT is handled by the caller)."""
    if value is _ABSENT:
        return "ABSENT"
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, (int, Decimal, float)):
        return "INTEGER" if isinstance(value, int) or is_decimal_integral(value) else "NUMBER"
    if isinstance(value, str):
        return "STRING"
    if isinstance(value, list):
        return "ARRAY"
    if isinstance(value, dict):
        return "OBJECT"
    return "ABSENT"


def json_type_satisfies(token: str, required: str) -> bool:
    return token == required or (required == "NUMBER" and token == "INTEGER")


def number_canonicalizable(value: Any) -> bool:
    try:
        rfc8785.dumps(float(value) if isinstance(value, Decimal) else value)
        return True
    except Exception:
        return False


def first_uncanonicalizable_number(document: Any) -> str | None:
    """Pointer of the first number in DESCENDANTS canonical preorder that RFC8785 cannot serialize."""
    # Each stack entry carries its location as a linked (parent location, token) pair, so visiting a node costs O(1) at any
    # nesting depth; the token list is materialized once, for the number found.
    stack: list[tuple[Any, Any]] = [(document, None)]
    while stack:
        value, trail = stack.pop()
        if isinstance(value, bool) or value is None or isinstance(value, str):
            continue
        if isinstance(value, (int, Decimal)):
            if not number_canonicalizable(value):
                tokens: list[str] = []
                while trail is not None:
                    trail, token = trail
                    tokens.append(token)
                tokens.reverse()
                return pointer_of(tokens)
        elif isinstance(value, dict):
            for key in sorted(value, key=utf16_key, reverse=True):
                stack.append((value[key], (trail, key)))
        elif isinstance(value, list):
            for index in range(len(value) - 1, -1, -1):
                stack.append((value[index], (trail, str(index))))
    return None


def contains_uncanonicalizable_number(document: Any) -> bool:
    return first_uncanonicalizable_number(document) is not None


def path_key(tokens: Sequence[Any]) -> tuple[Any, ...]:
    """DESCENDANTS canonical preorder key: a parent precedes its members, arrays ascend by index,
    object members ascend by UTF-16 code unit key order."""
    return tuple((0, token) if isinstance(token, int) else (1, utf16_key(str(token))) for token in tokens)


def schema_failures(validator: Any, instance: Any) -> list[Any]:
    return list(validator.iter_errors(instance))


def first_failure_tokens(errors: Sequence[Any]) -> list[Any] | None:
    """Instance location (token list) of the first failure in DESCENDANTS canonical preorder.

    A missing member is located at its containing object (the location reported by the validator);
    validator emission order is never used.
    """
    if not errors:
        return None
    best = min(errors, key=lambda error: path_key(list(error.absolute_path)))
    return list(best.absolute_path)


_SCHEMA_OBJECT_CACHE: dict[int, tuple[Any, Any]] = {}

# metacontract.json:/runtime_representation/schema_format_assertion (R5R4_SCHEMA_FORMAT_ASSERTION_DATE_TIME): `format: date-time` is
# ASSERTED (Draft 2020-12 Validation 7.2 and 7.3.1 with the RFC 3339 date-time grammar) in exactly the contexts of /applies_to:
# every SCHEMA_VALIDATE op node under either mode (/applies_to_scope/SCHEMA_VALIDATE) and every instance validated against a
# registered schema_ref during registration and eligibility (/applies_to_scope/REGISTERED_INSTANCE_VALIDATION). It is not asserted
# anywhere else (the caller's acceptance-profile schema, the metacontract's embedded value schemas, route-schema applicability);
# the pinned library has no date-time checker, so the grammar is asserted here. standard_domain_semantics: offset required; "T"/"Z"
# may be lower case (ABNF literals are case-insensitive, RFC 3339 5.6 NOTE); one or more fraction digits; -00:00 is valid syntax;
# only ASCII digits (the ABNF DIGIT rule). A non-string instance is outside the format (7.2). Only this declared format is
# asserted; the library's other format checkers stay off.
# Second 60 (standard_domain_semantics/leap_second and /leap_second_rule, R5R29A_R2C_LEAP_SECOND_TABLE_MEMBERSHIP): the string must
# satisfy every ordinary rule except the second bound; its date, time and numeric offset are normalized to the UTC leap second label
# (fraction removed; a fraction denotes a point inside the inserted second); it is a valid date-time iff that whole label is listed
# in the registered leap-second table. The table is governed input of the package under evaluation (Engine.leap_second_labels):
# never embedded here, never fetched, never refreshed. If it cannot be established (unregistered, unreadable, digest differing from
# the pin of /leap_second_rule/table_semantic_sha256) the assertion cannot be made and the run fails closed.
_RFC3339_DATE_TIME = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.[0-9]+)?(?:[Zz]|([+-])([0-9]{2}):([0-9]{2}))")


class LeapSecondTableUnavailable(ModelGap):
    """The registered leap-second table cannot be established as the pinned governed input (fails closed, never a pass)."""


_LEAP_SECOND_SOURCE: dict[str, Any] = {"engine": None}


def leap_second_labels() -> frozenset[str]:
    """The listed UTC leap second labels of the package under evaluation (LeapSecondTableUnavailable when not establishable)."""
    engine = _LEAP_SECOND_SOURCE["engine"]
    if engine is None:
        raise LeapSecondTableUnavailable("LEAP_SECOND_TABLE_UNAVAILABLE:NO_PACKAGE_UNDER_EVALUATION")
    return engine.leap_second_labels()


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        return 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
    return 30 if month in (4, 6, 9, 11) else 31


def rfc3339_date_time(value: Any) -> bool:
    """RFC 3339 5.6 `date-time` (full-date "T" full-time) as a yes/no assertion; True for every non-string instance."""
    if not isinstance(value, str):
        return True
    match = _RFC3339_DATE_TIME.fullmatch(value)
    if match is None:
        return False
    year, month, day, hour, minute, second = (int(match.group(i)) for i in range(1, 7))
    if not 1 <= month <= 12 or not 1 <= day <= _days_in_month(year, month) or hour > 23 or minute > 59 or second > 60:
        return False
    offset = 0
    if match.group(7) is not None:
        offset_hour, offset_minute = int(match.group(8)), int(match.group(9))
        if offset_hour > 23 or offset_minute > 59:
            return False
        offset = (offset_hour * 60 + offset_minute) * (1 if match.group(7) == "+" else -1)
    if second < 60:
        return True
    shift, minute_of_day = divmod(hour * 60 + minute - offset, 1440)  # the UTC time of day and the day shift of the normalization
    utc_year, utc_month, utc_day = year, month, day + shift
    if utc_day < 1:
        utc_month -= 1
        if utc_month < 1:
            utc_year, utc_month = utc_year - 1, 12
        utc_day = _days_in_month(utc_year, utc_month)
    elif utc_day > _days_in_month(utc_year, utc_month):
        utc_year, utc_month, utc_day = (utc_year + 1, 1, 1) if utc_month == 12 else (utc_year, utc_month + 1, 1)
    label = "%04d-%02d-%02dT%02d:%02d:60Z" % (utc_year, utc_month, utc_day, minute_of_day // 60, minute_of_day % 60)
    return label in leap_second_labels()


def _date_time_format_checker() -> Any:
    checker = jsonschema.FormatChecker(formats=())
    checker.checks("date-time")(rfc3339_date_time)
    return checker


DATE_TIME_FORMAT_CHECKER = _date_time_format_checker()


def validator_for(schema: Any, root: Any = None, registered: bool = False) -> Any:
    """Draft 2020-12 validator for `schema`; `root` (when given) is the resource that local $ref values resolve in. `registered`:
    the instance is validated against a registered schema_ref during registration and eligibility, the one context of this
    function that asserts the declared `date-time` format (schema_format_assertion/applies_to); every other use leaves
    `format` annotation-only."""
    key = (id(schema), id(root), registered)
    cached = _SCHEMA_OBJECT_CACHE.get(key)
    if cached is not None and cached[0] is schema:
        return cached[1]
    checker = DATE_TIME_FORMAT_CHECKER if registered else None
    validator = (jsonschema.Draft202012Validator(root, format_checker=checker).evolve(schema=schema) if root is not None
                 else jsonschema.Draft202012Validator(schema, format_checker=checker))
    _SCHEMA_OBJECT_CACHE[key] = (schema, validator)
    return validator


def metaschema_valid(document: Any) -> bool:
    """Is `document` a valid Draft 2020-12 schema? The library's check_schema question, answered by the explicit-stack walk
    (draft2020_schema_valid), so a schema document nested to any depth in real schema keywords ($defs, properties, ...) is judged
    without Python recursion per nesting level. Only the walk's own data conditions mean "not valid"."""
    try:
        return draft2020_schema_valid(document)
    except ExpressionError:
        return False
    except _D2020_DATA_ERRORS:
        return False


def local_fragment_reference_ok(document: Any, reference: Any) -> bool:
    """A $ref/$dynamicRef value that is a resolvable local RFC6901 fragment of `document`."""
    if not isinstance(reference, str) or not reference.startswith("#"):
        return False
    fragment = reference[1:]
    if re.search(r"%(?![0-9A-Fa-f]{2})", fragment):
        return False
    try:
        fragment = re.sub(rb"%([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]),
                          fragment.encode("utf-8")).decode("utf-8")
    except UnicodeDecodeError:
        return False
    if fragment != "" and not fragment.startswith("/"):
        return False
    try:
        return ptr_lookup(document, fragment) is not _ABSENT
    except Exception:
        return False


_INSTANCE_DATA_KEYWORDS = ("const", "enum", "default", "examples")


def first_nonlocal_reference(document: Any) -> str | None:
    """Pointer of the first $ref/$dynamicRef member, in DESCENDANTS canonical preorder, that is not a
    resolvable local RFC6901 fragment. Values of const/enum/default/examples are instance data, not schema
    keywords, and a dictionary value is a property named like a keyword, not a reference."""
    stack: list[tuple[Any, list[str]]] = [(document, [])]
    while stack:
        value, tokens = stack.pop()
        if isinstance(value, dict):
            children = []
            for key in sorted(value, key=utf16_key):
                child = value[key]
                if key in _INSTANCE_DATA_KEYWORDS and not (tokens and tokens[-1] in ("properties", "patternProperties", "$defs", "definitions", "dependentSchemas")):
                    continue
                if key in ("$ref", "$dynamicRef") and not isinstance(child, (dict, list)):
                    if not local_fragment_reference_ok(document, child):
                        return pointer_of(tokens + [key])
                children.append((child, tokens + [key]))
            stack.extend(reversed(children))
        elif isinstance(value, list):
            stack.extend((value[i], tokens + [str(i)]) for i in range(len(value) - 1, -1, -1))
    return None


def pattern_matches(pattern: str, value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return re.search(pattern[:-1] + r"\Z" if pattern.endswith("$") and not pattern.endswith("\\$") else pattern,
                         value) is not None
    except re.error:
        return False


def base64_strict(value: Any) -> bytes | None:
    """Strict RFC4648 base64 without whitespace; None when invalid."""
    if not isinstance(value, str):
        return None
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None


def canonical_relative_path(value: Any) -> bool:
    """CANONICAL_REPOSITORY_RELATIVE_FORWARD_SLASH: not absolute, no backslash, no empty, . or .. segment."""
    if not isinstance(value, str) or value == "" or "\\" in value:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    return not any(part in ("", ".", "..") for part in value.split("/"))


def read_relative(root: Path | None, value: Any) -> bytes:
    """Read a root-relative artifact; PathIneligible(NOT_CANONICAL | OUTSIDE_ROOT | UNREADABLE) otherwise."""
    if not canonical_relative_path(value):
        raise PathIneligible("NOT_CANONICAL")
    if root is None:
        raise PathIneligible("UNREADABLE")
    try:
        resolved_root = root.resolve()
        candidate = root.joinpath(*value.split("/")).resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise PathIneligible("UNREADABLE") from exc
    if resolved_root != candidate and resolved_root not in candidate.parents:
        raise PathIneligible("OUTSIDE_ROOT")
    try:
        return candidate.read_bytes()
    except (OSError, ValueError) as exc:
        raise PathIneligible("UNREADABLE") from exc


def safe_relative_file(root: Path, value: str) -> tuple[Path, str]:
    """Resolved path of a canonical root-relative file (PathIneligible otherwise)."""
    read_relative(root, value)
    return root.joinpath(*value.split("/")).resolve(), value


def set_extra_index(items: Sequence[Any], expected: set[Any]) -> int | None:
    """First extra element by ascending index: not in the expected set, or a repeat of an earlier element."""
    seen: set[Any] = set()
    for index, item in enumerate(items):
        if not isinstance(item, str) or item not in expected or item in seen:
            return index
        seen.add(item)
    return None



class _JcsSink:
    """Write-only sink for rfc8785.dump: collects the emitted byte fragments."""

    __slots__ = ("write",)

    def __init__(self, parts: list[bytes]) -> None:
        self.write = parts.append


_JCS_ESCAPED = re.compile(r'[\x00-\x1f\\"]')  # the characters RFC 8785 3.2.2.2 (as rfc8785 serializes it) escapes
_JCS_SAFE_INTEGER = 2 ** 53 - 1
_JCS_KEY_CACHE: dict[str, tuple[bytes, bytes]] = {}


def _jcs_serialize(root: Any) -> bytes:
    """RFC8785 bytes of `root` with Decimal numbers digested to floats and ResolvedObject values replaced by their public
    record, on an explicit stack of open containers: no Python recursion per nesting level, work proportional to the node
    count. Plain strings, small integers and the literals are written directly; every other scalar is written by
    rfc8785.dump itself; objects are ordered by UTF-16 code unit key order, exactly as rfc8785 does."""
    parts: list[bytes] = []
    emit = parts.append
    sink: Any = None
    keys = _JCS_KEY_CACHE
    stack: list[list[Any]] = []  # open containers: [members, next index, closing byte, is_object]
    node = root
    while True:
        kind = type(node)
        if kind is str:
            if _JCS_ESCAPED.search(node) is None:
                emit(b'"' + node.encode("utf-8") + b'"')
            else:
                sink = sink or _JcsSink(parts)
                rfc8785.dump(node, sink)
        elif kind is int and -_JCS_SAFE_INTEGER <= node <= _JCS_SAFE_INTEGER:
            emit(str(node).encode("ascii"))
        elif node is None:
            emit(b"null")
        elif node is True:
            emit(b"true")
        elif node is False:
            emit(b"false")
        else:
            while isinstance(node, ResolvedObject):
                node = node.public_record()
            if isinstance(node, Decimal):
                if not node.is_finite():
                    raise ValueError("nonfinite JSON number")
                number = float(node)
                if not math.isfinite(number):
                    raise ValueError("JSON number outside RFC8785 range")
                node = number
            if isinstance(node, dict):
                if node:
                    emit(b"{")
                    stack.append([sorted(node.items(), key=lambda kv: kv[0].encode("utf-16be")), 0, b"}", True])
                else:
                    emit(b"{}")
            elif isinstance(node, (list, tuple)):
                if node:
                    emit(b"[")
                    stack.append([node, 0, b"]", False])
                else:
                    emit(b"[]")
            else:
                sink = sink or _JcsSink(parts)
                rfc8785.dump(node, sink)
        # the next value to write: the next member of the innermost open container that has one left
        while True:
            if not stack:
                return b"".join(parts)
            frame = stack[-1]
            members, index, closing, is_object = frame
            if index == len(members):
                emit(closing)
                stack.pop()
                continue
            frame[1] = index + 1
            if is_object:
                key, node = members[index]
                text = keys.get(key)
                if text is None:
                    if len(keys) >= 4096:
                        keys.clear()
                    text = keys[key] = (rfc8785.dumps(key) + b":", b"," + rfc8785.dumps(key) + b":")
                emit(text[1] if index else text[0])
            else:
                node = members[index]
                if index:
                    emit(b",")
            break


def jcs_bytes(value: Any) -> bytes:
    if isinstance(value, (dict, list)):
        cached = _JCS_CACHE.get(id(value))
        if cached is not None and cached[0] is value:
            _JCS_CACHE.move_to_end(id(value))
            return cached[1]
    try:
        result = _jcs_serialize(value)
    except Exception as exc:
        raise ExpressionError("JCS_DOMAIN_ERROR") from exc
    if isinstance(value, (dict, list)):
        _JCS_CACHE[id(value)] = (value, result)
        _JCS_CACHE.move_to_end(id(value))
        while len(_JCS_CACHE) > 8192:
            _JCS_CACHE.popitem(last=False)
    return result


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_id(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


@lru_cache(maxsize=4096)
def pointer_tokens(pointer: str) -> list[str]:
    if not isinstance(pointer, str):
        raise ExpressionError("INVALID_JSON_POINTER")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise ExpressionError("INVALID_JSON_POINTER")
    out = []
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            raise ExpressionError("INVALID_JSON_POINTER")
        out.append(raw.replace("~1", "/").replace("~0", "~"))
    return out


def encode_pointer_token(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def get_pointer(value: Any, pointer: str) -> Any:
    tokens = pointer_tokens(pointer)
    node = value
    for token in tokens:
        if isinstance(node, ResolvedObject):
            node = node.public_record()
        if isinstance(node, dict):
            if token not in node:
                raise ExpressionError("POINTER_TARGET_MISSING", pointer)
            node = node[token]
        elif isinstance(node, list):
            if not token.isascii() or not token.isdigit() or (len(token) > 1 and token[0] == "0"):
                raise ExpressionError("INVALID_ARRAY_INDEX", pointer)
            index = int(token)
            if index >= len(node):
                raise ExpressionError("POINTER_TARGET_MISSING", pointer)
            node = node[index]
        else:
            raise ExpressionError("POINTER_NON_CONTAINER", pointer)
    def public_value(selected: Any) -> Any:
        if isinstance(selected, ResolvedObject):
            return selected.public_record()
        if isinstance(selected, list) and any(isinstance(item, ResolvedObject) for item in selected):
            return [public_value(item) for item in selected]
        if isinstance(selected, dict) and set(selected) == {"objects"} and isinstance(selected["objects"], list):
            return {"objects": public_value(selected["objects"])}
        return selected
    return public_value(node)


def remove_pointer(value: Any, pointer: str) -> None:
    tokens = pointer_tokens(pointer)
    if not tokens:
        raise ExpressionError("ROOT_EXCLUSION_FORBIDDEN", pointer)
    parent = value
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    leaf = tokens[-1]
    if isinstance(parent, dict):
        if leaf not in parent:
            raise ExpressionError("EXCLUDED_POINTER_MISSING", pointer)
        del parent[leaf]
    elif isinstance(parent, list):
        idx = int(leaf)
        if idx >= len(parent):
            raise ExpressionError("EXCLUDED_POINTER_MISSING", pointer)
        del parent[idx]
    else:
        raise ExpressionError("EXCLUDED_POINTER_PARENT_INVALID", pointer)


def _json_clone(value: Any) -> Any:
    """copy.deepcopy(value) for decoded JSON containers, on an explicit work stack: the same copy (insertion order, shared and
    cyclic references through a memo, every non-container value through copy.deepcopy), with no Python recursion per
    nesting level."""
    kind = type(value)
    if kind is not dict and kind is not list:
        return copy.deepcopy(value)
    memo: dict[int, Any] = {}
    root: Any = {} if kind is dict else []
    memo[id(value)] = root
    stack: list[tuple[Any, Any]] = [(value, root)]

    def child(item: Any) -> Any:
        item_kind = type(item)
        if item_kind is not dict and item_kind is not list:
            return copy.deepcopy(item, memo)
        known = memo.get(id(item))
        if known is None:
            known = memo[id(item)] = {} if item_kind is dict else []
            stack.append((item, known))
        return known

    while stack:
        source, target = stack.pop()
        if type(source) is dict:
            for key, item in source.items():
                target[key if type(key) is str else copy.deepcopy(key, memo)] = child(item)
        else:
            for item in source:
                target.append(child(item))
    return root


def semantic_digest(value: Any, exclusions: Sequence[str] = ()) -> str:
    clone = _json_clone(value)
    checked: list[list[str]] = []
    for path in exclusions:
        tokens = pointer_tokens(path)
        if any(tokens[:len(old)] == old or old[:len(tokens)] == tokens for old in checked):
            raise ExpressionError("OVERLAPPING_DIGEST_EXCLUSIONS", path)
        checked.append(tokens)
    for path in exclusions:
        remove_pointer(clone, path)
    return sha256(jcs_bytes(clone))


def identity(ref: Mapping[str, Any]) -> tuple[str, str, str]:
    return str(ref.get("kind", "")), str(ref.get("id", "")), str(ref.get("version", ""))


def ident_record(kind: str, object_id: str, version: str) -> dict[str, str]:
    return {"kind": kind, "id": object_id, "version": version}


def strict_set_equal(left: Sequence[Any], right: Sequence[Any]) -> bool:
    left_c = [jcs_bytes(x) for x in left]
    right_c = [jcs_bytes(x) for x in right]
    if len(set(left_c)) != len(left_c) or len(set(right_c)) != len(right_c):
        raise ExpressionError("DUPLICATE_SET_ITEM")
    return set(left_c) == set(right_c)


def compare_numbers(left: Any, right: Any, comparator: str) -> bool:
    numeric = (int, float, Decimal)
    if isinstance(left, bool) or isinstance(right, bool) or not isinstance(left, numeric) or not isinstance(right, numeric):
        raise ExpressionError("NUMERIC_TYPE_ERROR")
    try:
        a, b = Decimal(str(left)), Decimal(str(right))
    except InvalidOperation as exc:
        raise ExpressionError("NUMERIC_DOMAIN_ERROR") from exc
    if not a.is_finite() or not b.is_finite():
        raise ExpressionError("NUMERIC_DOMAIN_ERROR")
    operations = {"LT": a < b, "LTE": a <= b, "EQ": a == b, "NE": a != b, "GTE": a >= b, "GT": a > b}
    if comparator not in operations:
        raise ExpressionError("INVALID_COMPARATOR")
    return operations[comparator]

def json_equal(left: Any, right: Any) -> bool:
    """metacontract:/numeric_representation/json_equal: objects have the same keys with equal values (member order ignored),
    arrays the same length with equal values in order, numbers equal mathematical value, every other type exact type and value.
    The pair walk is an explicit stack of open containers, each holding the lazy iterator over its not yet compared child pairs
    (so the first mismatch ends the walk exactly where the structural definition does): no Python recursion per nesting level,
    work proportional to the node count, and the same result at every depth. JSON_EQUAL declares no error class, so there is no
    depth limit here (the traversal limit belongs to DESCENDANTS)."""
    numeric = (int, float, Decimal)
    open_pairs: list[Iterable[tuple[Any, Any]]] = [iter(((left, right),))]
    while open_pairs:
        for left, right in open_pairs[-1]:
            if isinstance(left, ResolvedObject):
                left = left.public_record()
            if isinstance(right, ResolvedObject):
                right = right.public_record()
            ln = isinstance(left, numeric) and not isinstance(left, bool)
            rn = isinstance(right, numeric) and not isinstance(right, bool)
            if ln or rn:
                if not ln or not rn or not Decimal(str(left)) == Decimal(str(right)):
                    return False
            elif isinstance(left, dict) and isinstance(right, dict):
                if left.keys() != right.keys():
                    return False
                if left:
                    open_pairs.append(zip(left.values(), map(right.__getitem__, left)))
                    break
            elif isinstance(left, list) and isinstance(right, list):
                if len(left) != len(right):
                    return False
                if left:
                    open_pairs.append(zip(left, right))
                    break
            elif type(left) is not type(right) or not left == right:
                return False
        else:
            open_pairs.pop()
    return True


_RFC3339 = re.compile(r"^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?(Z|[+-][0-9]{2}:[0-9]{2})$")


@lru_cache(maxsize=1024)
def timestamp_seconds(text: Any) -> Decimal:
    if not isinstance(text, str):
        raise ExpressionError("MALFORMED_RFC3339")
    match = _RFC3339.fullmatch(text)
    if not match:
        raise ExpressionError("MALFORMED_RFC3339")
    year, month, day, hour, minute, second = (int(match.group(i)) for i in range(1, 7))
    frac, zone = match.group(7), match.group(8)
    if second > 59 or hour > 23 or minute > 59 or (frac is not None and len(frac) > 9) or zone == "-00:00":
        raise ExpressionError("MALFORMED_RFC3339")
    try:
        ordinal = date(year, month, day).toordinal()
    except ValueError as exc:
        raise ExpressionError("MALFORMED_RFC3339") from exc
    offset = 0
    if zone != "Z":
        oh, om = int(zone[1:3]), int(zone[4:6])
        if oh > 23 or om > 59:
            raise ExpressionError("MALFORMED_RFC3339")
        offset = (oh * 60 + om) * (1 if zone[0] == "+" else -1)
    fractional = Decimal("0." + frac) if frac else Decimal(0)
    whole = Decimal((ordinal - date(1970, 1, 1).toordinal()) * 86400 + hour * 3600 + minute * 60 + second - offset * 60)
    normalized = whole + fractional
    low = Decimal((date(1, 1, 1).toordinal() - date(1970, 1, 1).toordinal()) * 86400)
    high = Decimal((date(9999, 12, 31).toordinal() - date(1970, 1, 1).toordinal()) * 86400 + 86399) + Decimal("0.999999999")
    if normalized < low or normalized > high:
        raise ExpressionError("DURATION_OVERFLOW")
    return normalized


def descendant_limits(resource_limits: Mapping[str, Any] | None = None) -> tuple[int, int]:
    source = resource_limits if isinstance(resource_limits, Mapping) else {}
    depth = source.get("max_json_traversal_depth", _DESCENDANT_LIMIT_BASELINES["max_json_traversal_depth"])
    nodes = source.get("max_json_nodes_visited_per_value", _DESCENDANT_LIMIT_BASELINES["max_json_nodes_visited_per_value"])
    return int(depth), int(nodes)


def set_descendant_limits(resource_limits: Mapping[str, Any] | None = None) -> None:
    global _DESCENDANT_LIMITS
    _DESCENDANT_LIMITS = descendant_limits(resource_limits)
    _DESCENDANT_CACHE.clear()


def descendants(root: Any, limits: tuple[int, int] | None = None) -> list[dict[str, Any]]:
    # Normative DESCENDANT_RECORD emission: preorder depth-first with an explicit LIFO stack,
    # every visited node emitted, object member keys ordered by UTF-16 code unit ascending,
    # array children in ascending canonical decimal index order, ancestor_pointers an
    # inclusive root-through-self chain ending at the node pointer, member_key the exact
    # object member name for object children and null for the root and array children.
    max_depth, max_nodes = limits if limits is not None else _DESCENDANT_LIMITS
    cache_key = (id(root), max_depth, max_nodes)
    cached = _DESCENDANT_CACHE.get(cache_key)
    if cached is not None and cached[0] is root:
        _DESCENDANT_CACHE.move_to_end(cache_key)
        return cached[1]
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    stack: list[tuple[Any, str, list[str], str | None, list[str]]] = [(root, "", [], None, [""])]
    count = 0
    while stack:
        value, ptr, tokens, member_key, ancestors = stack.pop()
        count += 1
        if len(tokens) > max_depth or count > max_nodes:
            raise ExpressionError("TRAVERSAL_RESOURCE_LIMIT", ptr)
        if ptr in seen:
            raise ExpressionError("NON_JSON_VALUE", ptr)
        seen.add(ptr)
        if value is None:
            kind = "NULL"
        elif isinstance(value, bool):
            kind = "BOOLEAN"
        elif isinstance(value, (int, float, Decimal)):
            if (isinstance(value, float) and (value != value or value == float("inf") or value == float("-inf"))) or (isinstance(value, Decimal) and not value.is_finite()):
                raise ExpressionError("NON_JSON_VALUE", ptr)
            kind = "NUMBER"
        elif isinstance(value, str):
            kind = "STRING"
        elif isinstance(value, list):
            kind = "ARRAY"
        elif isinstance(value, dict):
            kind = "OBJECT"
        else:
            raise ExpressionError("NON_JSON_VALUE", ptr)
        keys = sorted(value.keys(), key=lambda k: k.encode("utf-16-be")) if isinstance(value, dict) else []
        out.append({"pointer": ptr, "value": value, "path_tokens": tokens, "ancestor_pointers": ancestors,
                    "value_type": kind, "keys": keys, "member_key": member_key})
        children: list[tuple[Any, str, list[str], str | None, list[str]]] = []
        if isinstance(value, dict):
            for key in keys:
                child_ptr = ptr + "/" + encode_pointer_token(key)
                child_tokens = tokens + [key]
                children.append((value[key], child_ptr, child_tokens, key, ancestors + [child_ptr]))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                token = str(index)
                child_ptr = ptr + "/" + token
                children.append((child, child_ptr, tokens + [token], None, ancestors + [child_ptr]))
        stack.extend(reversed(children))
    if isinstance(root, (dict, list)):
        _DESCENDANT_CACHE[cache_key] = (root, out)
        _DESCENDANT_CACHE.move_to_end(cache_key)
        while len(_DESCENDANT_CACHE) > 64:
            _DESCENDANT_CACHE.popitem(last=False)
    return out


def descendant_record_conformance(registry: Any, limits: tuple[int, int] | None = None) -> list[str]:
    definition = registry.get("descendant_record") if isinstance(registry, dict) else None
    vectors = registry.get("descendant_conformance_vectors") if isinstance(registry, dict) else None
    if not isinstance(definition, dict):
        return ["DESCENDANT_RECORD definition is not an object"]
    if not isinstance(vectors, list) or len(vectors) != 9:
        return ["DESCENDANT_RECORD conformance vector count is not 9"]
    failures: list[str] = []
    fields = definition.get("fields") if isinstance(definition.get("fields"), dict) else {}
    shape = definition.get("record_shape") if isinstance(definition.get("record_shape"), dict) else {}
    emitted_order = list(descendants({}, limits)[0].keys())
    if list(shape.get("field_order", [])) != emitted_order or shape.get("field_count") != len(emitted_order):
        failures.append("record_shape field order disagrees with the emitted record")
    if sorted(fields) != sorted(emitted_order):
        failures.append("declared field set disagrees with the emitted record")
    for vector in vectors:
        if not isinstance(vector, dict):
            failures.append("conformance vector is not an object")
            continue
        vid = vector.get("vector_id", "")
        actual = descendants(vector.get("input"), limits)
        if len(actual) != vector.get("expected_record_count") or actual != vector.get("expected_records"):
            failures.append(str(vid) + ": emitted descendant records differ from the registered vector")
        for row in actual:
            chain = row["ancestor_pointers"]
            if not chain or chain[0] != "" or chain[-1] != row["pointer"]:
                failures.append(str(vid) + ": " + str(row["pointer"]) + " ancestor_pointers is not an inclusive root-through-self chain")
        probe = vector.get("ancestry_semantics_probe")
        if isinstance(probe, dict):
            observed = next((row["ancestor_pointers"] for row in actual if row["pointer"] == probe.get("probe_pointer")), None)
            if (probe.get("selected_semantics") != "INCLUSIVE_ROOT_THROUGH_SELF"
                    or observed != probe.get("inclusive_expected_ancestor_pointers")
                    or observed == probe.get("strict_expected_ancestor_pointers")):
                failures.append(str(vid) + ": inclusive versus strict ancestry probe did not resolve to inclusive")
        exclusion = vector.get("exclusion_probe")
        if isinstance(exclusion, dict):
            excluded = exclusion.get("excluded_pointer")
            excluded_nodes = [row["pointer"] for row in actual if excluded in row["ancestor_pointers"]]
            included_nodes = [row["pointer"] for row in actual if excluded not in row["ancestor_pointers"]]
            if (excluded_nodes != exclusion.get("expected_excluded_node_pointers")
                    or included_nodes != exclusion.get("expected_included_node_pointers")):
                failures.append(str(vid) + ": excluded-prefix governing token did not resolve by exact ancestor-pointer equality")
    return failures


# ---------------------------------------------------------------------------
# SCHEMA_VALIDATE: JSON Schema Draft 2020-12 validity on an explicit stack.
# primitive-registry:/primitives/SCHEMA_VALIDATE declares a BOOLEAN result ("JSON Schema Draft 2020-12; local fragment refs
# only; no retrieval"), the error classes of a malformed schema, an unresolved local fragment and an unsupported dialect, and
# no structural or traversal bound (max_json_traversal_depth belongs to DESCENDANTS). The answer therefore cannot depend on how
# deeply the instance or the schema is nested, and the depth of the Python call stack must never decide it. The keyword
# semantics below are the pinned library's (keywords of a schema object in member order, the first failing keyword ends that
# schema, the library's type checker, number comparisons, regular-expression search, format checker and reference
# resolver); only the control flow differs: every step into a subschema or a subinstance is a request that one driver loop
# serves from a list of suspended evaluations kept on the heap, so no Python frame is added per nesting level. The meta-schema walk
# resolves its vocabulary references with the library's resolver; the walk of a SCHEMA_VALIDATE operand resolves the admitted local
# pointers against the root of the operand itself (see the decision procedure below).
# ---------------------------------------------------------------------------
_D2020_EVAL, _D2020_PROPERTIES, _D2020_ITEMS = 0, 1, 2
_D2020_UNRESOLVABLE = jsonschema.validators.referencing.exceptions.Unresolvable
# Data conditions of a malformed schema (an operator the instance cannot take, an unusable member); resource exhaustion is not one.
_D2020_DATA_ERRORS = (TypeError, ValueError, ArithmeticError, AttributeError, LookupError, re.error,
                      jsonschema.exceptions.UnknownType)
_D2020_META: dict[str, Any] = {}


class _D2020Identity:
    """The `$id` of a subschema in the form the library's resolver takes it (scope of relative references)."""

    __slots__ = ("identifier",)

    def __init__(self, identifier: Any):
        self.identifier = identifier

    def id(self) -> Any:
        return self.identifier


def _d2020_scalar_key(value: Any) -> tuple[Any, ...] | None:
    """Hashable identity under JSON equality for a scalar, None for an array or an object."""
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, (int, float, Decimal)):
        return ("number", Decimal(str(value)))
    if isinstance(value, str):
        return ("string", value)
    return None


def _d2020_type(walk, types, instance, schema):
    return any(walk.validator.is_type(instance, each) for each in ([types] if isinstance(types, str) else types))


def _d2020_enum(walk, enums, instance, schema):
    return any(json_equal(each, instance) for each in enums)


def _d2020_const(walk, const, instance, schema):
    return json_equal(instance, const)


def _d2020_minimum(walk, bound, instance, schema):
    return not (walk.validator.is_type(instance, "number") and instance < bound)


def _d2020_maximum(walk, bound, instance, schema):
    return not (walk.validator.is_type(instance, "number") and instance > bound)


def _d2020_exclusive_minimum(walk, bound, instance, schema):
    return not (walk.validator.is_type(instance, "number") and instance <= bound)


def _d2020_exclusive_maximum(walk, bound, instance, schema):
    return not (walk.validator.is_type(instance, "number") and instance >= bound)


def _d2020_multiple_of(walk, divisor, instance, schema):
    if not walk.validator.is_type(instance, "number"):
        return True
    if isinstance(divisor, float):
        quotient = instance / divisor
        try:
            return int(quotient) == quotient
        except OverflowError:  # the quotient is not a float: decide on the exact rational numbers
            numerator, denominator = instance.as_integer_ratio()
            divisor_numerator, divisor_denominator = divisor.as_integer_ratio()
            return (numerator * divisor_denominator) % (denominator * divisor_numerator) == 0
    return not instance % divisor


def _d2020_min_length(walk, bound, instance, schema):
    return not (isinstance(instance, str) and len(instance) < bound)


def _d2020_max_length(walk, bound, instance, schema):
    return not (isinstance(instance, str) and len(instance) > bound)


def _d2020_pattern(walk, pattern, instance, schema):
    return not (isinstance(instance, str) and re.search(pattern, instance) is None)


def _d2020_format(walk, name, instance, schema):
    if name == "date-time" and walk.date_time:  # the declared SCHEMA_VALIDATE assertion (schema_format_assertion/applies_to)
        return rfc3339_date_time(instance)
    if walk.format_checker is None:
        return True
    try:
        walk.format_checker.check(instance, name)
    except jsonschema.exceptions.FormatError:
        return False
    return True


def _d2020_min_items(walk, bound, instance, schema):
    return not (isinstance(instance, list) and len(instance) < bound)


def _d2020_max_items(walk, bound, instance, schema):
    return not (isinstance(instance, list) and len(instance) > bound)


def _d2020_unique_items(walk, unique, instance, schema):
    if not unique or not isinstance(instance, list):
        return True
    scalars: set[tuple[Any, ...]] = set()
    containers: list[Any] = []
    for item in instance:
        key = _d2020_scalar_key(item)
        if key is None:
            if any(type(item) is type(earlier) and json_equal(earlier, item) for earlier in containers):
                return False
            containers.append(item)
        elif key in scalars:
            return False
        else:
            scalars.add(key)
    return True


def _d2020_min_properties(walk, bound, instance, schema):
    return not (isinstance(instance, dict) and len(instance) < bound)


def _d2020_max_properties(walk, bound, instance, schema):
    return not (isinstance(instance, dict) and len(instance) > bound)


def _d2020_required(walk, names, instance, schema):
    return not isinstance(instance, dict) or all(name in instance for name in names)


def _d2020_dependent_required(walk, dependencies, instance, schema):
    if not isinstance(instance, dict):
        return True
    return all(each in instance for name, needed in dependencies.items() if name in instance for each in needed)


_D2020_LEAF_KEYWORDS = {
    "type": _d2020_type, "enum": _d2020_enum, "const": _d2020_const, "minimum": _d2020_minimum, "maximum": _d2020_maximum,
    "exclusiveMinimum": _d2020_exclusive_minimum, "exclusiveMaximum": _d2020_exclusive_maximum,
    "multipleOf": _d2020_multiple_of, "minLength": _d2020_min_length, "maxLength": _d2020_max_length,
    "pattern": _d2020_pattern, "format": _d2020_format, "minItems": _d2020_min_items, "maxItems": _d2020_max_items,
    "uniqueItems": _d2020_unique_items, "minProperties": _d2020_min_properties, "maxProperties": _d2020_max_properties,
    "required": _d2020_required, "dependentRequired": _d2020_dependent_required,
}


def _d2020_reference(walk, reference, instance, schema, resolver):
    return (yield from walk.follow(resolver, reference, instance))


def _d2020_all_of(walk, subschemas, instance, schema, resolver):
    for subschema in subschemas:
        if not (yield (_D2020_EVAL, subschema, instance, resolver, True)):
            return False
    return True


def _d2020_any_of(walk, subschemas, instance, schema, resolver):
    for subschema in subschemas:
        if (yield (_D2020_EVAL, subschema, instance, resolver, True)):
            return True
    return False


def _d2020_one_of(walk, subschemas, instance, schema, resolver):
    branches = iter(subschemas)
    for subschema in branches:
        if (yield (_D2020_EVAL, subschema, instance, resolver, True)):
            for other in branches:
                if (yield (_D2020_EVAL, other, instance, resolver, False)):
                    return False
            return True
    return False


def _d2020_not(walk, subschema, instance, schema, resolver):
    return not (yield (_D2020_EVAL, subschema, instance, resolver, False))


def _d2020_if(walk, condition, instance, schema, resolver):
    if (yield (_D2020_EVAL, condition, instance, resolver, False)):
        if "then" in schema:
            return (yield (_D2020_EVAL, schema["then"], instance, resolver, True))
    elif "else" in schema:
        return (yield (_D2020_EVAL, schema["else"], instance, resolver, True))
    return True


def _d2020_properties(walk, properties, instance, schema, resolver):
    if not isinstance(instance, dict):
        return True
    for name, subschema in properties.items():
        if name in instance and not (yield (_D2020_EVAL, subschema, instance[name], resolver, True)):
            return False
    return True


def _d2020_pattern_properties(walk, patterns, instance, schema, resolver):
    if not isinstance(instance, dict):
        return True
    for pattern, subschema in patterns.items():
        for name, member in instance.items():
            if re.search(pattern, name) and not (yield (_D2020_EVAL, subschema, member, resolver, True)):
                return False
    return True


def _d2020_additional_properties(walk, additional, instance, schema, resolver):
    if not isinstance(instance, dict):
        return True
    properties = schema.get("properties", {})
    patterns = "|".join(schema.get("patternProperties", {}))
    extras = [name for name in instance if name not in properties and not (patterns and re.search(patterns, name))]
    if isinstance(additional, dict):
        for name in extras:
            if not (yield (_D2020_EVAL, additional, instance[name], resolver, True)):
                return False
        return True
    return bool(additional) or not extras


def _d2020_property_names(walk, subschema, instance, schema, resolver):
    if not isinstance(instance, dict):
        return True
    for name in instance:
        if not (yield (_D2020_EVAL, subschema, name, resolver, True)):
            return False
    return True


def _d2020_prefix_items(walk, subschemas, instance, schema, resolver):
    if not isinstance(instance, list):
        return True
    for item, subschema in zip(instance, subschemas):
        if not (yield (_D2020_EVAL, subschema, item, resolver, True)):
            return False
    return True


def _d2020_items(walk, subschema, instance, schema, resolver):
    if not isinstance(instance, list):
        return True
    prefix = len(schema.get("prefixItems", []))
    if len(instance) <= prefix:
        return True
    if subschema is False:
        return False
    for index in range(prefix, len(instance)):
        if not (yield (_D2020_EVAL, subschema, instance[index], resolver, True)):
            return False
    return True


def _d2020_contains(walk, subschema, instance, schema, resolver):
    if not isinstance(instance, list):
        return True
    least = schema.get("minContains", 1)
    most = schema.get("maxContains", len(instance))
    matches = 0
    for item in instance:
        if (yield (_D2020_EVAL, subschema, item, resolver, False)):
            matches += 1
            if matches > most:
                return False
    return not matches < least


def _d2020_dependent_schemas(walk, dependencies, instance, schema, resolver):
    if not isinstance(instance, dict):
        return True
    for name, subschema in dependencies.items():
        if name in instance and not (yield (_D2020_EVAL, subschema, instance, resolver, True)):
            return False
    return True


def _d2020_unevaluated_properties(walk, subschema, instance, schema, resolver):
    if not isinstance(instance, dict):
        return True
    evaluated = set((yield (_D2020_PROPERTIES, instance, schema, resolver)))
    for name in instance:
        if name not in evaluated and not (yield (_D2020_EVAL, subschema, instance[name], resolver, True)):
            return False
    return True


def _d2020_unevaluated_items(walk, subschema, instance, schema, resolver):
    if not isinstance(instance, list):
        return True
    evaluated = set((yield (_D2020_ITEMS, instance, schema, resolver)))
    return all(index in evaluated for index in range(len(instance)))


_D2020_APPLICATOR_KEYWORDS = {
    "$ref": _d2020_reference, "$dynamicRef": _d2020_reference, "allOf": _d2020_all_of, "anyOf": _d2020_any_of,
    "oneOf": _d2020_one_of, "not": _d2020_not, "if": _d2020_if, "properties": _d2020_properties,
    "patternProperties": _d2020_pattern_properties, "additionalProperties": _d2020_additional_properties,
    "propertyNames": _d2020_property_names, "prefixItems": _d2020_prefix_items, "items": _d2020_items,
    "contains": _d2020_contains, "dependentSchemas": _d2020_dependent_schemas,
    "unevaluatedProperties": _d2020_unevaluated_properties, "unevaluatedItems": _d2020_unevaluated_items,
}


_D2020_NO_ROOT = object()


class _D2020Resolved:
    """A reference target in the form the walk consumes it (`contents`, and the `resolver` for references met inside it)."""

    __slots__ = ("contents", "resolver")

    def __init__(self, contents: Any, resolver: Any):
        self.contents = contents
        self.resolver = resolver


class _Draft2020Walk:
    """One validity question: does `instance` satisfy `schema`? `validator` is the library validator whose type checker and
    reference resolver define the dialect, `format_checker` asserts `format` (None: annotation only), `date_time` asserts the declared
    `date-time` format (SCHEMA_VALIDATE walks only), `memoize` records the answer for a (referenced schema, instance node) pair, which
    is a pure function of the pair when the schema document has no dynamic-scope keyword. A reference met again for the same pair
    while still open can never finish (the schema depends on itself without descending into the instance): that schema is
    malformed. `local_root` (SCHEMA_VALIDATE): every `$ref` is an admitted local JSON Pointer fragment and resolves against that
    root alone (reference_admissibility/resolution_base); no `$id` or anchor takes part, no library resolver is involved."""

    __slots__ = ("validator", "format_checker", "memo", "open_references", "local_root", "date_time", "failure_paths")

    def __init__(self, validator: Any, format_checker: Any, memoize: bool, local_root: Any = _D2020_NO_ROOT, date_time: bool = False):
        self.validator = validator
        self.format_checker = format_checker
        self.memo: dict[tuple[int, int], tuple[Any, Any, bool]] | None = {} if memoize else None
        self.open_references: set[tuple[int, ...]] = set()
        self.local_root = local_root
        self.date_time = date_time
        self.failure_paths: list[tuple[Any, ...]] = []

    def run(self, schema: Any, instance: Any, resolver: Any) -> bool:
        return self.drive(self._evaluate(schema, instance, resolver, False))

    def drive(self, first: Any) -> Any:
        """Serve the requests of one evaluation (and of the evaluations it opens) from a list of suspended generators."""
        suspended = [first]
        answer: Any = None
        while suspended:
            try:
                request = suspended[-1].send(answer)
            except StopIteration as finished:
                suspended.pop()
                answer = finished.value
                continue
            if request[0] == _D2020_EVAL:
                suspended.append(self._evaluate(*request[1:]))
            elif request[0] == _D2020_PROPERTIES:
                suspended.append(self._evaluated_properties(*request[1:]))
            else:
                suspended.append(self._evaluated_items(*request[1:]))
            answer = None
        return answer

    def lookup(self, resolver: Any, reference: Any) -> Any:
        if self.local_root is not _D2020_NO_ROOT:
            tokens = admitted_reference_tokens(reference)
            if tokens is None:  # only reachable through a target outside every schema position (data used as a schema)
                raise ExpressionError("SCHEMA_MALFORMED")
            target = lookup(self.local_root, tokens)
            if target is _ABSENT:
                raise ExpressionError("SCHEMA_FRAGMENT_UNRESOLVED")
            return _D2020Resolved(target, None)
        try:
            return resolver.lookup(reference)
        except _D2020_UNRESOLVABLE as exc:
            raise ExpressionError("SCHEMA_FRAGMENT_UNRESOLVED") from exc

    def follow(self, resolver: Any, reference: Any, instance: Any):
        resolved = self.lookup(resolver, reference)
        target = resolved.contents
        key = (id(target), id(instance))
        if self.memo is not None:
            known = self.memo.get(key)
            if known is not None and known[0] is target and known[1] is instance:
                return known[2]
        if key in self.open_references:
            raise ExpressionError("SCHEMA_MALFORMED")
        self.open_references.add(key)
        answer = yield (_D2020_EVAL, target, instance, resolved.resolver, False)
        self.open_references.discard(key)
        if self.memo is not None:
            self.memo[key] = (target, instance, answer)
        return answer

    def follow_annotations(self, request: int, resolver: Any, reference: Any, instance: Any):
        """The member names or item indexes evaluated through a reference (same open-reference guard as `follow`)."""
        resolved = self.lookup(resolver, reference)
        key = (id(resolved.contents), id(instance), request)
        if key in self.open_references:
            raise ExpressionError("SCHEMA_MALFORMED")
        self.open_references.add(key)
        evaluated = yield (request, instance, resolved.contents, resolved.resolver)
        self.open_references.discard(key)
        return evaluated

    def _evaluate(self, schema: Any, instance: Any, resolver: Any, enter: bool):
        """`enter`: the schema is a subschema met by descent, so its own `$id` opens a new scope for relative references."""
        if schema is True or schema is False:
            return schema
        if not isinstance(schema, dict):
            raise ExpressionError("SCHEMA_MALFORMED")
        if enter and "$id" in schema and self.local_root is _D2020_NO_ROOT:
            resolver = resolver.in_subresource(_D2020Identity(schema["$id"]))
        for keyword, value in schema.items():
            leaf = _D2020_LEAF_KEYWORDS.get(keyword)
            if leaf is not None:
                if not leaf(self, value, instance, schema):
                    return False
                continue
            applicator = _D2020_APPLICATOR_KEYWORDS.get(keyword)
            if applicator is not None and not (yield from applicator(self, value, instance, schema, resolver)):
                return False
        return True

    # -- first failure location (the library's top-level failures, DESCENDANTS canonical preorder) ----------------------------
    def valid(self, schema: Any, instance: Any, resolver: Any, enter: bool) -> bool:
        """The boolean answer for a branch the failure walk has to decide (anyOf): its own evaluation on the heap."""
        return _Draft2020Walk(self.validator, self.format_checker, False, self.local_root, self.date_time).drive(
            self._evaluate(schema, instance, resolver, enter))

    def first_failure_path(self, schema: Any, instance: Any, resolver: Any) -> list[Any] | None:
        """Location (list of tokens) of the first failure in DESCENDANTS canonical preorder among the library's top-level failures
        of `instance` against `schema` (list(iter_errors) absolute paths; a missing member is located at its containing object,
        the failure of an anyOf at the instance it applies to); None when `instance` is valid. Every step into a subschema or a
        subinstance is a request served from a heap list of suspended generators, so the nesting depth of `instance` is never
        a Python call depth. Defined for the keywords of the Draft 2020-12 meta-schema; any other applying keyword is a model gap."""
        self.failure_paths = []
        suspended = [self._collect(schema, instance, resolver, False, ())]
        while suspended:
            try:
                request = next(suspended[-1])
            except StopIteration:
                suspended.pop()
                continue
            suspended.append(self._collect(*request))
        return list(min(self.failure_paths, key=path_key)) if self.failure_paths else None

    def _collect(self, schema: Any, instance: Any, resolver: Any, enter: bool, path: tuple[Any, ...]):
        if schema is True:
            return
        if schema is False:
            self.failure_paths.append(path)
            return
        if not isinstance(schema, dict):
            raise ExpressionError("SCHEMA_MALFORMED")
        if enter and "$id" in schema and self.local_root is _D2020_NO_ROOT:
            resolver = resolver.in_subresource(_D2020Identity(schema["$id"]))
        for keyword, value in schema.items():
            leaf = _D2020_LEAF_KEYWORDS.get(keyword)
            if leaf is not None:
                if not leaf(self, value, instance, schema):
                    self.failure_paths.append(path)  # the failure of a keyword that does not descend is located at the instance
                continue
            if keyword not in _D2020_APPLICATOR_KEYWORDS:
                continue
            if keyword in ("$ref", "$dynamicRef"):
                resolved = self.lookup(resolver, value)
                yield (resolved.contents, instance, resolved.resolver, False, path)
            elif keyword == "allOf":
                for subschema in value:
                    yield (subschema, instance, resolver, True, path)
            elif keyword == "anyOf":
                if not any(self.valid(subschema, instance, resolver, True) for subschema in value):
                    self.failure_paths.append(path)
            elif keyword == "properties":
                if isinstance(instance, dict):
                    for name, subschema in value.items():
                        if name in instance:
                            yield (subschema, instance[name], resolver, True, path + (name,))
            elif keyword == "additionalProperties":
                if isinstance(instance, dict):
                    properties = schema.get("properties", {})
                    patterns = "|".join(schema.get("patternProperties", {}))
                    extras = [name for name in instance if name not in properties and not (patterns and re.search(patterns, name))]
                    if isinstance(value, dict):
                        for name in extras:
                            yield (value, instance[name], resolver, True, path + (name,))
                    elif not value and extras:
                        self.failure_paths.append(path)
            elif keyword == "propertyNames":
                if isinstance(instance, dict):
                    for name in instance:
                        yield (value, name, resolver, True, path)
            elif keyword == "items":
                if isinstance(instance, list):
                    prefix = len(schema.get("prefixItems", []))
                    if len(instance) > prefix:
                        if value is False:
                            self.failure_paths.append(path)
                        else:
                            for index in range(prefix, len(instance)):
                                yield (value, instance[index], resolver, True, path + (index,))
            else:
                raise ModelGap("METASCHEMA_FAILURE_LOCATION_KEYWORD_UNSUPPORTED:" + keyword)

    def _evaluated_properties(self, instance: Any, schema: Any, resolver: Any):
        """Member names of the object `instance` that the keywords of `schema` (and of the subschemas valid for it) evaluate."""
        if isinstance(schema, bool):
            return []
        names: list[str] = []
        for keyword in ("$ref", "$dynamicRef"):
            if schema.get(keyword) is not None:
                names += yield from self.follow_annotations(_D2020_PROPERTIES, resolver, schema[keyword], instance)
        if isinstance(schema.get("properties"), dict):
            names += [name for name in schema["properties"] if name in instance]
        for keyword in ("additionalProperties", "unevaluatedProperties"):
            if schema.get(keyword) is not None:
                for name, member in instance.items():
                    if (yield (_D2020_EVAL, schema[keyword], member, resolver, True)):
                        names.append(name)
        if "patternProperties" in schema:
            names += [name for name in instance for pattern in schema["patternProperties"] if re.search(pattern, name)]
        if "dependentSchemas" in schema:
            for name, subschema in schema["dependentSchemas"].items():
                if name in instance:
                    names += yield (_D2020_PROPERTIES, instance, subschema, resolver)
        for keyword in ("allOf", "oneOf", "anyOf"):
            if keyword in schema:
                for subschema in schema[keyword]:
                    if (yield (_D2020_EVAL, subschema, instance, resolver, True)):
                        names += yield (_D2020_PROPERTIES, instance, subschema, resolver)
        if "if" in schema:
            if (yield (_D2020_EVAL, schema["if"], instance, resolver, False)):
                names += yield (_D2020_PROPERTIES, instance, schema["if"], resolver)
                if "then" in schema:
                    names += yield (_D2020_PROPERTIES, instance, schema["then"], resolver)
            elif "else" in schema:
                names += yield (_D2020_PROPERTIES, instance, schema["else"], resolver)
        return names

    def _evaluated_items(self, instance: Any, schema: Any, resolver: Any):
        """Indexes of the array `instance` that the keywords of `schema` (and of the subschemas valid for it) evaluate."""
        if isinstance(schema, bool):
            return []
        if "items" in schema:
            return list(range(len(instance)))
        indexes: list[int] = []
        for keyword in ("$ref", "$dynamicRef"):
            if schema.get(keyword) is not None:
                indexes += yield from self.follow_annotations(_D2020_ITEMS, resolver, schema[keyword], instance)
        if "prefixItems" in schema:
            indexes += range(len(schema["prefixItems"]))
        if "if" in schema:
            if (yield (_D2020_EVAL, schema["if"], instance, resolver, False)):
                indexes += yield (_D2020_ITEMS, instance, schema["if"], resolver)
                if "then" in schema:
                    indexes += yield (_D2020_ITEMS, instance, schema["then"], resolver)
            elif "else" in schema:
                indexes += yield (_D2020_ITEMS, instance, schema["else"], resolver)
        for keyword in ("contains", "unevaluatedItems"):
            if keyword in schema:
                for index, item in enumerate(instance):
                    if (yield (_D2020_EVAL, schema[keyword], item, resolver, False)):
                        indexes.append(index)
        for keyword in ("allOf", "oneOf", "anyOf"):
            if keyword in schema:
                for subschema in schema[keyword]:
                    if (yield (_D2020_EVAL, subschema, instance, resolver, True)):
                        indexes += yield (_D2020_ITEMS, instance, subschema, resolver)
        return indexes


def _d2020_meta() -> Any:
    library = jsonschema.Draft202012Validator
    meta = _D2020_META.get("validator")
    if meta is None:
        meta = _D2020_META["validator"] = library(library.META_SCHEMA, format_checker=library.FORMAT_CHECKER)
    return meta


def draft2020_schema_valid(schema: Any) -> bool:
    """Is `schema` a valid Draft 2020-12 schema (the meta-schema asserts `format`)? The library's check_schema, without recursion."""
    library = jsonschema.Draft202012Validator
    meta = _d2020_meta()
    return _Draft2020Walk(meta, library.FORMAT_CHECKER, False).run(library.META_SCHEMA, schema, meta._resolver)


def metaschema_first_failure_tokens(document: Any) -> list[Any] | None:
    """Location of the first failure in DESCENDANTS canonical preorder when `document` is not a valid Draft 2020-12 schema (the
    library's top-level meta-schema failures, first_failure_tokens(list(iter_errors))), None when it is valid; computed on the
    heap, so a document nested to any depth in real schema keywords is located exactly and without Python recursion."""
    library = jsonschema.Draft202012Validator
    meta = _d2020_meta()
    return _Draft2020Walk(meta, library.FORMAT_CHECKER, False).first_failure_path(library.META_SCHEMA, document, meta._resolver)


# ---------------------------------------------------------------------------
# SCHEMA_VALIDATE decision procedure. primitive-registry:/primitives/SCHEMA_VALIDATE (HUMAN_RULING_2026_10_05_R5R29A_R2C and _EDGE):
#   /error_precedence  1 representation and schema shape, 2 dialect, 3 whole-schema admissibility (keyword value forms, structural
#                      schema validity, only the admitted $ref form, no active $dynamicRef, no embedded-$id-dependent reference),
#                      4 local JSON Pointer fragment resolution, 5 instance validation (the boolean);
#   /within_step_selection  no semantic rank among the conditions of one step: the owning location is the first in DESCENDANTS
#                      canonical preorder of the schema operand (and resolution starts only after the whole schema is admissible);
#   /schema_position   a keyword is active only as a member of an object at a schema position (the root, and every value reached
#                      from a schema position through a Draft 2020-12 schema-valued keyword); members of const, enum, default,
#                      examples or any other non-schema value are data; an embedded schema resource is a non-root schema position
#                      whose object declares $id;
#   /dialect_selection absent $schema selects Draft 2020-12; a $schema that is not a string, not an RFC 3986 URI with a scheme or not
#                      normalized (RFC 3986 6.2.2) is MALFORMED_SCHEMA; any other value than the supported identifier is
#                      UNSUPPORTED_DIALECT; every $schema at a schema position is subject to this;
#   /reference_admissibility  a $ref is admitted iff it is exactly `#` or `#` + a fragment that begins with `/`, is RFC 3986 fragment
#                      syntax and whose percent-decoded value is an RFC 6901 pointer; any other $ref, any $dynamicRef, and any admitted
#                      reference located inside an embedded schema resource or whose pointer path from the root enters one is
#                      MALFORMED_SCHEMA; anchors are inert; an admitted reference resolves against the root of the operand and a
#                      missing target is UNRESOLVED_LOCAL_FRAGMENT.
# Everything here runs on explicit stacks: no Python recursion per nesting level of the schema or of the instance.
# ---------------------------------------------------------------------------
_SCHEMA_POSITION_SINGLE = frozenset(("additionalProperties", "items", "contains", "propertyNames", "unevaluatedItems",
                                     "unevaluatedProperties", "not", "if", "then", "else", "contentSchema"))
_SCHEMA_POSITION_ARRAY = frozenset(("prefixItems", "allOf", "anyOf", "oneOf"))
_SCHEMA_POSITION_OBJECT = frozenset(("properties", "patternProperties", "dependentSchemas", "$defs"))

# RFC 3986 URI (Appendix A), ASCII only.
_URI_PCT = r"%[0-9A-Fa-f]{2}"
_URI_UNRESERVED = r"A-Za-z0-9\-._~"
_URI_SUB_DELIMS = r"!$&'()*+,;="
_URI_PCHAR = r"(?:[" + _URI_UNRESERVED + _URI_SUB_DELIMS + r":@]|" + _URI_PCT + r")"
_URI_H16 = r"[0-9A-Fa-f]{1,4}"
_URI_IPV4 = r"(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])"
_URI_LS32 = r"(?:" + _URI_H16 + ":" + _URI_H16 + "|" + _URI_IPV4 + ")"
_URI_IPV6 = "(?:" + "|".join((
    "(?:" + _URI_H16 + ":){6}" + _URI_LS32,
    "::(?:" + _URI_H16 + ":){5}" + _URI_LS32,
    "(?:" + _URI_H16 + ")?::(?:" + _URI_H16 + ":){4}" + _URI_LS32,
    "(?:(?:" + _URI_H16 + ":){0,1}" + _URI_H16 + ")?::(?:" + _URI_H16 + ":){3}" + _URI_LS32,
    "(?:(?:" + _URI_H16 + ":){0,2}" + _URI_H16 + ")?::(?:" + _URI_H16 + ":){2}" + _URI_LS32,
    "(?:(?:" + _URI_H16 + ":){0,3}" + _URI_H16 + ")?::" + _URI_H16 + ":" + _URI_LS32,
    "(?:(?:" + _URI_H16 + ":){0,4}" + _URI_H16 + ")?::" + _URI_LS32,
    "(?:(?:" + _URI_H16 + ":){0,5}" + _URI_H16 + ")?::" + _URI_H16,
    "(?:(?:" + _URI_H16 + ":){0,6}" + _URI_H16 + ")?::")) + ")"
_URI_HOST = (r"\[(?:" + _URI_IPV6 + r"|v[0-9A-Fa-f]+\.[" + _URI_UNRESERVED + _URI_SUB_DELIMS + r":]+)\]|" + _URI_IPV4
             + r"|(?:[" + _URI_UNRESERVED + _URI_SUB_DELIMS + r"]|" + _URI_PCT + r")*")
_URI = re.compile(
    r"(?P<scheme>[A-Za-z][A-Za-z0-9+\-.]*):"
    r"(?://(?:(?P<userinfo>(?:[" + _URI_UNRESERVED + _URI_SUB_DELIMS + r":]|" + _URI_PCT + r")*)@)?(?P<host>" + _URI_HOST
    + r")(?::(?P<port>[0-9]*))?(?P<abempty>(?:/" + _URI_PCHAR + r"*)*)"
    r"|(?P<absolute>/(?:" + _URI_PCHAR + r"+(?:/" + _URI_PCHAR + r"*)*)?)"
    r"|(?P<rootless>" + _URI_PCHAR + r"+(?:/" + _URI_PCHAR + r"*)*)"
    r"|)"
    r"(?:\?(?P<query>(?:" + _URI_PCHAR + r"|[/?])*))?"
    r"(?:#(?P<fragment>(?:" + _URI_PCHAR + r"|[/?])*))?", re.ASCII)


def _remove_dot_segments(path: str) -> str:
    """RFC 3986 5.2.4."""
    remaining, output = path, ""
    while remaining:
        if remaining.startswith("../"):
            remaining = remaining[3:]
        elif remaining.startswith("./"):
            remaining = remaining[2:]
        elif remaining.startswith("/./"):
            remaining = remaining[2:]
        elif remaining == "/.":
            remaining = "/"
        elif remaining.startswith("/../"):
            remaining, output = remaining[3:], output.rpartition("/")[0]
        elif remaining == "/..":
            remaining, output = "/", output.rpartition("/")[0]
        elif remaining in (".", ".."):
            remaining = ""
        else:
            cut = remaining.find("/", 1 if remaining.startswith("/") else 0)
            segment, remaining = (remaining, "") if cut == -1 else (remaining[:cut], remaining[cut:])
            output += segment
    return output


def _uri_is_normalized(text: str, match: "re.Match[str]") -> bool:
    """text equals its RFC 3986 6.2.2 syntax-based normalization: lower-case scheme and host, upper-case percent-encoding hex
    digits, no percent-encoded unreserved character, no dot segment (6.2.2.1 to 6.2.2.3)."""
    if match["scheme"] != match["scheme"].lower():
        return False
    if match["host"] is not None:
        host = re.sub(_URI_PCT, "", match["host"])
        if host != host.lower():
            return False
    for triplet in re.finditer(r"%([0-9A-Fa-f]{2})", text):
        digits = triplet.group(1)
        if digits != digits.upper() or re.fullmatch(r"[A-Za-z0-9\-._~]", chr(int(digits, 16))):
            return False
    path = match["abempty"] or match["absolute"] or match["rootless"] or ""
    return _remove_dot_segments(path) == path


def schema_dollar_schema_fault(value: Any) -> str | None:
    """dialect_selection for one `$schema` value: SCHEMA_MALFORMED (not a string, not an absolute URI, not normalized),
    SCHEMA_DIALECT_UNSUPPORTED (a valid normalized URI other than the supported identifier), None (the supported identifier)."""
    if not isinstance(value, str):
        return "SCHEMA_MALFORMED"
    match = _URI.fullmatch(value)
    if match is None or not _uri_is_normalized(value, match):
        return "SCHEMA_MALFORMED"
    return None if value == DRAFT_2020_12 else "SCHEMA_DIALECT_UNSUPPORTED"


_REF_FRAGMENT = re.compile(r"(?:[A-Za-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9A-Fa-f]{2})*", re.ASCII)
_JSON_POINTER_SYNTAX = re.compile(r"(?:/(?:[^~/]|~[01])*)*")


def admitted_reference_tokens(reference: Any) -> list[str] | None:
    """Tokens of the RFC 6901 pointer an admitted `$ref` denotes, None when the reference is not admitted: exactly `#`, or `#`
    followed by a fragment that begins with `/`, is RFC 3986 fragment syntax and whose percent-decoded UTF-8 value is a valid
    RFC 6901 JSON Pointer (reference_admissibility/admitted_ref_grammar)."""
    if not isinstance(reference, str) or not reference.startswith("#"):
        return None
    fragment = reference[1:]
    if fragment == "":
        return []
    if not fragment.startswith("/") or _REF_FRAGMENT.fullmatch(fragment) is None:
        return None
    try:
        decoded = re.sub(rb"%([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]), fragment.encode("ascii")).decode("utf-8")
    except UnicodeDecodeError:
        return None
    return pointer_tokens(decoded) if _JSON_POINTER_SYNTAX.fullmatch(decoded) is not None else None


def _reference_enters_embedded_resource(root: Any, tokens: Sequence[str]) -> bool:
    """Does the pointer path from the root pass through (or end at) an embedded schema resource, i.e. a non-root schema position
    whose object declares `$id`? A path through data (const, enum, ...) enters no schema position."""
    node, state = root, "S"
    for token in tokens:
        child = lookup(node, [token])
        if child is _ABSENT:
            return False
        if state == "S":
            state = ("S" if token in _SCHEMA_POSITION_SINGLE else "A" if token in _SCHEMA_POSITION_ARRAY
                     else "O" if token in _SCHEMA_POSITION_OBJECT else "D")
        elif state in ("A", "O"):
            state = "S"
        else:
            return False
        if state == "S" and isinstance(child, dict) and "$id" in child:
            return True
        if (state == "S" and not isinstance(child, dict)) or (state == "A" and not isinstance(child, list)) \
                or (state == "O" and not isinstance(child, dict)) or state == "D":
            return False
        node = child
    return False


def _schema_positions(root: Any):
    """(object, trail, inside) for the root and every object reached from a schema position through a schema-valued keyword, on an
    explicit stack. `trail` is the linked (parent trail, token) path of the object, None for the root; `inside` tells whether the
    object is, or lies inside, an embedded schema resource."""
    stack: list[tuple[Any, Any, bool]] = [(root, None, False)]
    while stack:
        node, trail, inside = stack.pop()
        if not isinstance(node, dict):
            continue
        inside = inside or (trail is not None and "$id" in node)
        yield node, trail, inside
        for key, value in node.items():
            if key in _SCHEMA_POSITION_SINGLE:
                stack.append((value, (trail, key), inside))
            elif key in _SCHEMA_POSITION_ARRAY:
                if isinstance(value, list):
                    stack.extend((item, ((trail, key), index), inside) for index, item in enumerate(value))
            elif key in _SCHEMA_POSITION_OBJECT:
                if isinstance(value, dict):
                    stack.extend((item, ((trail, key), name), inside) for name, item in value.items())


def _trail_tokens(trail: Any, member: str) -> list[Any]:
    tokens: list[Any] = []
    while trail is not None:
        trail, token = trail
        tokens.append(token)
    tokens.reverse()
    tokens.append(member)
    return tokens


def _local_ref_location(root: Any, tokens: Sequence[str]) -> tuple[Any, ...]:
    """The resolved path, retaining integer indexes for array locations."""
    location: list[Any] = []
    node = root
    for token in tokens:
        location.append(int(token) if isinstance(node, list) else token)
        node = lookup(node, [token])
    return tuple(location)


def _earlier_fault(current: Any, tokens: list[Any], token: str) -> Any:
    """Keep the fault whose location is first in DESCENDANTS canonical preorder (within_step_selection)."""
    key = path_key(tokens)
    return current if current is not None and current[0] <= key else (key, tokens, token)


def schema_admission_fault(schema: Any) -> tuple[str, list[Any]] | None:
    """Steps 1 to 4 of SCHEMA_VALIDATE/error_precedence for the schema operand: (internal failure token, location tokens of the
    owning fault) or None when the operand is admissible and every admitted reference resolves. Tokens: SCHEMA_MALFORMED ->
    MALFORMED_SCHEMA, SCHEMA_DIALECT_UNSUPPORTED -> UNSUPPORTED_DIALECT, SCHEMA_FRAGMENT_UNRESOLVED -> UNRESOLVED_LOCAL_FRAGMENT."""
    key = id(schema)
    cached = _SCHEMA_ADMISSION.get(key)
    if cached is not None and cached[0] is schema:
        _SCHEMA_ADMISSION.move_to_end(key)
        return cached[1]
    fault = _schema_admission_fault(schema)
    _SCHEMA_ADMISSION[key] = (schema, fault)
    _SCHEMA_ADMISSION.move_to_end(key)
    while len(_SCHEMA_ADMISSION) > 256:
        _SCHEMA_ADMISSION.popitem(last=False)
    return fault


def _schema_admission_fault(schema: Any) -> tuple[str, list[Any]] | None:
    if not isinstance(schema, (dict, bool)):  # step 1: representation and schema shape
        return ("SCHEMA_MALFORMED", [])
    dialect = admissibility = resolution = None
    # A resolved pointer can designate an object originally carried as data (for
    # example under const). Once referenced, that object is a schema target and
    # its own active references belong to the local-reference graph. Paths, not
    # object identities, are the vertices: the JSON operand cannot alias nodes.
    pending: list[tuple[Any, tuple[Any, ...]]] = [(schema, ())]
    seen: set[tuple[Any, ...]] = set()
    edges: dict[tuple[Any, ...], tuple[Any, ...]] = {}
    ref_locations: dict[tuple[Any, ...], list[Any]] = {}
    while pending:
        subtree, prefix = pending.pop()
        for node, trail, inside in _schema_positions(subtree):
            path = prefix + tuple(_trail_tokens(trail, "")[:-1])
            if path in seen:
                continue
            seen.add(path)
            if "$schema" in node:
                token = schema_dollar_schema_fault(node["$schema"])
                if token is not None:
                    dialect = _earlier_fault(dialect, list(path) + ["$schema"], token)
            if "$dynamicRef" in node:
                admissibility = _earlier_fault(admissibility, list(path) + ["$dynamicRef"], "SCHEMA_MALFORMED")
            reference = node.get("$ref")
            if not isinstance(reference, str):
                continue  # the Draft meta-schema checks malformed keyword values
            owner = list(path) + ["$ref"]
            tokens = admitted_reference_tokens(reference)
            if tokens is None or inside or _reference_enters_embedded_resource(schema, tokens):
                admissibility = _earlier_fault(admissibility, owner, "SCHEMA_MALFORMED")
                continue
            target = lookup(schema, tokens)
            if target is _ABSENT:
                resolution = _earlier_fault(resolution, owner, "SCHEMA_FRAGMENT_UNRESOLVED")
            elif not isinstance(target, (dict, bool)) or (isinstance(target, dict) and not draft2020_schema_valid(target)):
                resolution = _earlier_fault(resolution, owner, "SCHEMA_MALFORMED")
            else:
                target_path = _local_ref_location(schema, tokens)
                edges[path] = target_path
                ref_locations[path] = owner
                if isinstance(target, dict) and target_path not in seen:
                    pending.append((target, target_path))
    if dialect is not None:  # step 2
        return (dialect[2], dialect[1])
    if not draft2020_schema_valid(schema):  # step 3, structural schema validity
        located = metaschema_first_failure_tokens(schema)
        if located is None:
            raise ModelGap("METASCHEMA_FAILURE_LOCATION_UNAVAILABLE")
        admissibility = _earlier_fault(admissibility, located, "SCHEMA_MALFORMED")
    if admissibility is not None:
        return (admissibility[2], admissibility[1])
    # Step 4 rejects every direct or indirect cycle before instance validation.
    # Each schema object has at most one active $ref, so following edges from
    # each source locates every cycle without recursion or instance dependence.
    examined: set[tuple[Any, ...]] = set()
    for source in edges:
        if source in examined:
            continue
        trail: list[tuple[Any, ...]] = []
        index: dict[tuple[Any, ...], int] = {}
        current = source
        while current in edges and current not in examined and current not in index:
            index[current] = len(trail)
            trail.append(current)
            current = edges[current]
        if current in index:
            for participant in trail[index[current]:]:
                resolution = _earlier_fault(resolution, ref_locations[participant], "SCHEMA_MALFORMED")
        examined.update(trail)
    if resolution is not None:
        return (resolution[2], resolution[1])
    return None


_D2020_TYPES = jsonschema.Draft202012Validator(True)


def draft2020_instance_valid(schema: Any, instance: Any) -> bool:
    """Step 5: the Draft 2020-12 boolean for an admissible schema whose references all resolve (declared `date-time` asserted)."""
    return _Draft2020Walk(_D2020_TYPES, None, True, schema, True).run(schema, instance, None)


def schema_is_valid(schema: Any, instance: Any, mode: str) -> bool:
    """SCHEMA_VALIDATE (see the decision procedure above). A fault of steps 1 to 4 is reported under the declared error class
    of the primitive (MALFORMED_SCHEMA, UNSUPPORTED_DIALECT, UNRESOLVED_LOCAL_FRAGMENT) and no other; both modes apply steps 1
    to 4; INSTANCE mode then answers the Draft 2020-12 boolean at any nesting depth of the schema and of the instance
    (draft2020_schema_valid and draft2020_instance_valid keep their open evaluations on the heap). A schema that depends on
    itself without descending into the instance, and a data condition the keyword operators cannot take, are MALFORMED_SCHEMA."""
    try:
        fault = schema_admission_fault(schema)
        if fault is not None:
            raise ExpressionError(fault[0])
        if mode == "META_SCHEMA":
            return True
        if mode != "INSTANCE":
            raise ExpressionError("INVALID_SCHEMA_MODE")
        return draft2020_instance_valid(schema, instance)
    except ExpressionError:
        raise
    except _D2020_DATA_ERRORS as exc:
        raise ExpressionError("SCHEMA_MALFORMED") from exc


def member_matches(content: Any, member_id: str, registration: Mapping[str, Any]) -> list[Any]:
    members = registration.get("members", [])
    if not isinstance(members, list):
        return []
    return [member_id for declared in members if declared == member_id]


# Internal pointer-traversal failure token -> the GET error class declared by primitive-registry:/primitives/GET/error_behavior.
GET_ERROR_CLASS_MAP = {
    "POINTER_TARGET_MISSING": "MISSING_PATH",
    "POINTER_NON_CONTAINER": "MISSING_PATH",
    "INVALID_JSON_POINTER": "INVALID_POINTER",
    "INVALID_ARRAY_INDEX": "INVALID_ARRAY_INDEX",
}


# Internal schema-validation failure token -> the SCHEMA_VALIDATE error class declared by
# primitive-registry:/primitives/SCHEMA_VALIDATE/error_behavior (the only three: nothing else may be reported): a schema that is not
# an admissible Draft 2020-12 schema operand (shape, malformed $schema, non-admitted $ref, active $dynamicRef, embedded-$id dependent
# reference, structural invalidity; or that depends on itself without descending into the instance) is MALFORMED_SCHEMA, an admitted
# local fragment without a target is UNRESOLVED_LOCAL_FRAGMENT, a well-formed $schema other than the supported identifier is
# UNSUPPORTED_DIALECT (decision procedure: schema_admission_fault).
SCHEMA_VALIDATE_ERROR_CLASS_MAP = {"SCHEMA_MALFORMED": "MALFORMED_SCHEMA", "SCHEMA_FRAGMENT_UNRESOLVED": "UNRESOLVED_LOCAL_FRAGMENT",
                                   "SCHEMA_DIALECT_UNSUPPORTED": "UNSUPPORTED_DIALECT"}


class Interpreter:
    def __init__(self, primitives: Mapping[str, Any], resource_limits: Mapping[str, Any] | None = None,
                 resolved_object_schema: Mapping[str, Any] | None = None,
                 schema_objects: Mapping[tuple[str, str, str], ResolvedObject] | None = None,
                 metacontract: Mapping[str, Any] | None = None):
        set_descendant_limits(resource_limits)
        self.allowed_ops = set(primitives)
        self.primitive_rows = {key: value for key, value in primitives.items() if isinstance(value, Mapping)}
        self.schema_objects = dict(schema_objects or {})
        self.metacontract = metacontract if isinstance(metacontract, Mapping) else {}
        self.procedure_positions: dict[str, int] = {}
        self.witness_law_owner: ResolvedObject | None = None
        self.assertions_evaluated = 0
        self.resolved_object_validator = (jsonschema.Draft202012Validator(resolved_object_schema)
                                          if resolved_object_schema is not None else None)

    def resolve_one(self, universe: Any, ref: Any) -> ResolvedObject:
        if not isinstance(ref, dict) or set(ref) - {"kind", "id", "version", "member_id"} or not all(
            isinstance(ref.get(k), str) and ref[k] for k in ("kind", "id", "version")
        ):
            raise ExpressionError("INVALID_TYPED_REFERENCE", ref)
        if "member_id" in ref and (not isinstance(ref["member_id"], str) or not ref["member_id"]):
            raise ExpressionError("INVALID_TYPED_REFERENCE", ref)
        if not isinstance(universe, dict) or set(universe) != {"objects"} or not isinstance(universe["objects"], list):
            raise ExpressionError("INVALID_UNIVERSE")
        matches = [obj for obj in universe["objects"] if isinstance(obj, ResolvedObject) and identity(obj.ref) == identity(ref)]
        if len(matches) != 1:
            raise ExpressionError("RESOLUTION_NOT_FOUND" if not matches else "RESOLUTION_AMBIGUOUS", ref)
        obj = matches[0]
        if "member_id" in ref:
            found = member_matches(obj.content, ref["member_id"], obj.registration)
            if len(found) != 1:
                raise ExpressionError("MEMBER_NOT_FOUND" if not found else "RESOLUTION_AMBIGUOUS", ref)
        return ResolvedObject(obj.ref, obj.registration, obj.content, obj.raw_bytes, obj.canonical_path,
                              obj.source_universe, dict(ref))

    def _typed_reference_fail(self, error_class: str, diagnostic: str, operand: Any = None) -> None:
        declared = self.primitive_rows.get("ENUMERATE_TYPED_REFERENCES", {})
        if error_class not in declared.get("error_behavior", {}).get("error_classes", []):
            error_class = "REFERENCE_DOMAIN_UNDERDETERMINED"
        raise ExpressionError(error_class, {"diagnostic": diagnostic, "operand": operand})

    @staticmethod
    def _same_typed_reference(left: Any, right: Any) -> bool:
        return isinstance(left, Mapping) and isinstance(right, Mapping) and jcs_bytes(dict(left)) == jcs_bytes(dict(right))

    @staticmethod
    def _ref_key(ref: Any) -> tuple[str, str, str, str]:
        if not isinstance(ref, Mapping):
            return ("", "", "", "")
        return tuple(str(ref.get(key, "")) for key in ("kind", "id", "version", "member_id"))

    def _member_law(self, error_class: str, diagnostic: str) -> SchemaMemberLaw:
        # The binding named by RESOLVE_ONE member resolution in the candidate metacontract.
        construction = self.metacontract.get("runtime_representation", {}).get("resolved_construction", {})
        reference = construction.get("member_resolution", {}).get("schema_member_binding_ref") if isinstance(construction, Mapping) else None
        try:
            return declared_member_law(self.metacontract, reference)
        except ValueError:
            self._typed_reference_fail(error_class, diagnostic)
            raise

    def _bind_reference_definitions(self, universe: Any, ref_type: Mapping[str, Any]) -> dict[tuple[str, str, str, str], str]:
        """reference-model.json:/reference_type/definition_binding, before any owner is selected.

        Array order; each definition names an exact SCHEMA owner in the explicit
        universe whose registered members contain its member_id exactly once, and
        its definition_pointer is exactly the pointer the declared member law
        builds from that member_id and which resolves in the same owner content.
        """
        law = self._member_law("REFERENCE_DOMAIN_UNDERDETERMINED", "MEMBER_BINDING_DECLARATION_UNAVAILABLE")
        definitions = ref_type.get("definition_refs")
        declaration = ref_type.get("definition_binding")
        if not isinstance(definitions, list):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_DEFINITION_DOMAIN_INVALID")
        expected = {
            "binding_ref": law.reference,
            "binding_phase": "BEFORE_OWNER_SELECTION;EVERY_DECLARED_DEFINITION_REF_IN_ARRAY_ORDER",
            "owner_selector": "reference_definition_ref_KIND_ID_VERSION",
            "required_owner_kind": law.registry_kind,
            "owner_resolution": "RESOLVE_ONE_SEMANTICS_AGAINST_THE_EXPLICIT_VERIFICATION_UNIVERSE_ARGUMENT",
            "member_id_required": True,
            "member_selection": "EXACTLY_ONE_EQUAL_STRING_IN_THE_RESOLVED_SCHEMA_OBJECT_REGISTERED_members",
            "definition_target": "THE_SELECTED_MEMBER_BINDING_POINTER_IN_THE_SAME_RESOLVED_SCHEMA_CONTENT",
            "definition_pointer_role": "DECLARED_EXPLICIT_PROJECTION_OF_THE_MEMBER_BINDING_POINTER",
            "definition_pointer_equality": "EXACT_JSON_STRING_EQUALITY_TO_THE_MEMBER_BINDING_POINTER",
            "raw_local_defs_lookup_without_registration": "FORBIDDEN",
            "binding_failure": {"primitive_id": "ENUMERATE_TYPED_REFERENCES", "error_class": "REFERENCE_DOMAIN_UNDERDETERMINED", "fail_closed": True},
            "bound_definition_count": len(definitions),
        }
        if not isinstance(declaration, Mapping) or dict(declaration) != expected:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "DEFINITION_BINDING_DECLARATION_UNSUPPORTED")
        bound: dict[tuple[str, str, str, str], str] = {}
        for row in definitions:
            if not isinstance(row, Mapping) or set(row) != {"reference_definition_ref", "definition_pointer"}:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_DEFINITION_ROW_INVALID", row)
            ref = row["reference_definition_ref"]
            member = ref.get("member_id") if isinstance(ref, Mapping) else None
            if not isinstance(ref, Mapping) or ref.get("kind") != law.registry_kind or not isinstance(member, str) or not member:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "DEFINITION_OWNER_NOT_A_REGISTERED_MEMBER_REFERENCE", ref)
            key = self._ref_key(ref)
            if key in bound:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_DEFINITION_IDENTITY_INVALID", ref)
            try:
                owner_obj = self.resolve_one(universe, dict(ref))
            except ExpressionError:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "DEFINITION_MEMBER_NOT_REGISTERED", ref)
            if row["definition_pointer"] != law.pointer_for(member):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "DEFINITION_POINTER_IS_NOT_THE_MEMBER_BINDING", ref)
            if law.locate(owner_obj.content, member) is REGISTRATION_CONTENT_ABSENT:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "DEFINITION_MEMBER_BINDING_UNRESOLVED", ref)
            bound[key] = row["definition_pointer"]
        return bound

    @staticmethod
    def _fragment_pointer(reference: Any) -> str | None:
        # Local URI-fragment JSON Pointer, strictly percent-decoded; None when not local or malformed.
        if not isinstance(reference, str) or not reference.startswith("#"):
            return None
        fragment = reference[1:]
        if re.search(r"%(?![0-9A-Fa-f]{2})", fragment):
            return None
        try:
            return re.sub(rb"%([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]), fragment.encode("utf-8")).decode("utf-8")
        except UnicodeDecodeError:
            return None

    def _enum_contract(self) -> tuple[str, str]:
        primitive = self.primitive_rows.get("ENUMERATE_TYPED_REFERENCES")
        calculus = self.metacontract.get("runtime_representation", {}).get("static_type_calculus", {})
        operator = calculus.get("operator_rules", {}).get("operators", {}).get("ENUMERATE_TYPED_REFERENCES")
        inventory = calculus.get("inventory", {}).get("normalized_static_paths", [])
        if not isinstance(primitive, Mapping) or not isinstance(operator, Mapping) or not isinstance(inventory, list):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ENUMERATION_CONTRACT_UNAVAILABLE")
        args, slots = primitive.get("arguments"), operator.get("slots")
        if (not isinstance(args, list) or not isinstance(slots, list) or
                [x.get("name") for x in args if isinstance(x, Mapping)] !=
                [x[0] for x in slots if isinstance(x, list) and x] or
                primitive.get("output_type") != operator.get("result")):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ENUMERATION_DECLARATION_MISMATCH")
        owner_ref = primitive.get("owner_universe_ref")
        owner_rows = [x.split(" = ", 1)[1] for x in inventory if isinstance(x, str) and
                      x.startswith("ENUMERATE_TYPED_REFERENCES:owner-universe = ")]
        route_rows = [x.split(" = ", 1)[1] for x in inventory if isinstance(x, str) and
                      x.startswith("ENUMERATE_TYPED_REFERENCES:route-applications = ")]
        if not isinstance(owner_ref, str) or owner_rows != [owner_ref] or len(route_rows) != 1:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ENUMERATION_STATIC_INVENTORY_MISMATCH")
        try:
            owner_pointer = owner_ref.split(":", 1)[1]
            route_pointer = route_rows[0].split(":", 1)[1]
            pointer_tokens(owner_pointer)
            pointer_tokens(route_pointer)
            if not owner_pointer.startswith("/") or not route_pointer.startswith("/"):
                raise ValueError("NOT_ABSOLUTE_POINTER")
        except (IndexError, ValueError, ExpressionError):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ENUMERATION_STATIC_POINTER_INVALID")
        return owner_pointer, route_pointer

    def _schema_accepts(self, resource_root: Any, schema_node: Any, value: Any) -> bool:
        try:
            return jsonschema.Draft202012Validator(resource_root).evolve(schema=schema_node).is_valid(value)
        except Exception as exc:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_APPLICATOR_UNSUPPORTED",
                                       type(exc).__name__)
        return False

    def _route_instances(self, resource_root: Any, applied_root: Any, owner_value: Any,
                         schema_pointer: str, declared_tokens: Any) -> list[tuple[Any, str]]:
        if not isinstance(schema_pointer, str) or not isinstance(declared_tokens, list):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "INVALID_ROUTE_APPLICATION")
        try:
            schema_path = pointer_tokens(schema_pointer)
        except ExpressionError:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "INVALID_ROUTE_POINTER", schema_pointer)
        steps: list[tuple[str, Any, Any, Any]] = []
        branches: list[tuple[int, str, Any, Any]] = []
        current = applied_root
        i = 0
        while i < len(schema_path):
            if not isinstance(current, Mapping):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_POINTER_NOT_SCHEMA", schema_pointer)
            part = schema_path[i]
            if part in ("properties", "patternProperties", "prefixItems"):
                if i + 1 >= len(schema_path):
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "INCOMPLETE_SCHEMA_ROUTE", schema_pointer)
                name, collection = schema_path[i + 1], current.get(part)
                if part == "prefixItems":
                    if not isinstance(collection, list) or not name.isascii() or not name.isdigit() or (len(name) > 1 and name[0] == "0"):
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "PREFIX_ITEM_SCHEMA_ROUTE_INVALID", schema_pointer)
                    child = collection[int(name)] if int(name) < len(collection) else None
                else:
                    if not isinstance(collection, Mapping) or name not in collection:
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_ROUTE_TARGET_MISSING", schema_pointer)
                    child = collection[name]
                steps.append((part, name, current, child))
                current = child
                i += 2
                continue
            if part in ("items", "contains", "additionalProperties", "unevaluatedProperties", "unevaluatedItems"):
                if part not in current:
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_ROUTE_TARGET_MISSING", schema_pointer)
                child = current[part]
                steps.append((part, None, current, child))
                current = child
                i += 1
                continue
            if part in ("allOf", "anyOf", "oneOf"):
                if i + 1 >= len(schema_path) or not isinstance(current.get(part), list):
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_BRANCH_ROUTE_INVALID", schema_pointer)
                branch_text = schema_path[i + 1]
                if not branch_text.isascii() or not branch_text.isdigit() or (len(branch_text) > 1 and branch_text[0] == "0"):
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_BRANCH_INDEX_INVALID", branch_text)
                branch_rows, branch_index = current[part], int(branch_text)
                if branch_index >= len(branch_rows):
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_BRANCH_INDEX_INVALID", branch_text)
                branches.append((len(steps), part, branch_rows, branch_index))
                current = branch_rows[branch_index]
                i += 2
                continue
            if part == "dependentSchemas":
                if i + 1 >= len(schema_path) or not isinstance(current.get(part), Mapping):
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "DEPENDENT_SCHEMA_ROUTE_INVALID", schema_pointer)
                dep = schema_path[i + 1]
                if dep not in current[part]:
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "DEPENDENT_SCHEMA_ROUTE_INVALID", dep)
                branches.append((len(steps), "dependentSchemas", dep, current[part][dep]))
                current = current[part][dep]
                i += 2
                continue
            if part in ("if", "then", "else"):
                if part == "if":
                    if part not in current:
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "CONDITIONAL_SCHEMA_ROUTE_INVALID", schema_pointer)
                    branches.append((len(steps), "if", current[part], True))
                    current = current[part]
                else:
                    condition = current.get("if")
                    if condition is None or part not in current:
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "CONDITIONAL_SCHEMA_ROUTE_INVALID", schema_pointer)
                    branches.append((len(steps), part, condition, current[part]))
                    current = current[part]
                i += 1
                continue
            if part in ("not", "propertyNames"):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "NEGATIVE_OR_NAME_SCHEMA_ROUTE_UNSUPPORTED", schema_pointer)
            if isinstance(current, Mapping) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isascii() and part.isdigit() and int(part) < len(current):
                current = current[int(part)]
            else:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_POINTER_TARGET_MISSING", schema_pointer)
            i += 1
        if len(declared_tokens) < len(steps):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_INSTANCE_ROUTE_MISMATCH", schema_pointer)
        route_offset = len(declared_tokens) - len(steps)
        for (keyword, name, _, _), token in zip(steps, declared_tokens[route_offset:]):
            expected = {"properties": "PROPERTY", "patternProperties": "PATTERN_PROPERTY", "prefixItems": "ARRAY_INDEX",
                        "additionalProperties": "ADDITIONAL_PROPERTY", "unevaluatedProperties": "ADDITIONAL_PROPERTY",
                        "items": "ARRAY_ITEM", "contains": "ARRAY_ITEM", "unevaluatedItems": "ARRAY_ITEM"}[keyword]
            if not isinstance(token, Mapping) or token.get("kind") != expected:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_INSTANCE_ROUTE_MISMATCH", token)
            if keyword in ("properties", "patternProperties", "prefixItems") and str(token.get("value")) != name:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_INSTANCE_ROUTE_MISMATCH", token)
            if keyword in ("additionalProperties", "unevaluatedProperties", "items", "contains", "unevaluatedItems") and "value" in token:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_INSTANCE_ROUTE_MISMATCH", token)
        states: list[tuple[Any, str]] = [(owner_value, "")]
        for token in declared_tokens[:route_offset]:
            if not isinstance(token, Mapping):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "INVALID_INSTANCE_PATH_TOKEN", token)
            kind = token.get("kind")
            value = token.get("value")
            selected_prefix: list[tuple[Any, str]] = []
            for instance, pointer in states:
                if kind == "PROPERTY" and isinstance(value, str) and isinstance(instance, dict) and value in instance:
                    selected_prefix.append((instance[value], pointer + "/" + encode_pointer_token(value)))
                elif kind == "PATTERN_PROPERTY" and isinstance(value, str) and isinstance(instance, dict):
                    try:
                        pattern = re.compile(value)
                    except re.error as exc:
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "UNSUPPORTED_SCHEMA_PATTERN", str(exc))
                    selected_prefix.extend((instance[key], pointer + "/" + encode_pointer_token(key))
                                           for key in sorted(instance, key=lambda x: x.encode("utf-16-be")) if pattern.search(key))
                elif kind == "ARRAY_ITEM" and "value" not in token and isinstance(instance, list):
                    selected_prefix.extend((item, pointer + "/" + str(index)) for index, item in enumerate(instance))
                elif kind == "ARRAY_INDEX" and (isinstance(value, str) or isinstance(value, int)) and not isinstance(value, bool):
                    index_text = str(value)
                    if not index_text.isascii() or not index_text.isdigit() or (len(index_text) > 1 and index_text[0] == "0"):
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "INVALID_ARRAY_INDEX_ROUTE", value)
                    index = int(index_text)
                    if isinstance(instance, list) and index < len(instance):
                        selected_prefix.append((instance[index], pointer + "/" + str(index)))
                elif kind == "ADDITIONAL_PROPERTY":
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "UNRESOLVED_ADDITIONAL_PROPERTY_PREFIX", schema_pointer)
            states = selected_prefix
        for step_index in range(len(steps) + 1):
            for position, branch_kind, branch_data, branch_value in branches:
                if position != step_index:
                    continue
                kept = []
                for instance, pointer in states:
                    if branch_kind in ("allOf", "anyOf", "oneOf"):
                        valid = [self._schema_accepts(resource_root, branch, instance) for branch in branch_data]
                        active = all(valid) if branch_kind == "allOf" else (
                            valid[branch_value] if branch_kind == "anyOf" else sum(valid) == 1 and valid[branch_value])
                    elif branch_kind == "dependentSchemas":
                        active = isinstance(instance, dict) and branch_data in instance
                    elif branch_kind == "if":
                        active = self._schema_accepts(resource_root, branch_data, instance)
                    else:
                        condition = self._schema_accepts(resource_root, branch_data, instance)
                        active = condition if branch_kind == "then" else not condition
                    if active:
                        kept.append((instance, pointer))
                states = kept
            if step_index == len(steps):
                break
            keyword, name, parent_schema, child_schema = steps[step_index]
            token = declared_tokens[route_offset + step_index]
            selected: list[tuple[Any, str]] = []
            for instance, pointer in states:
                if keyword == "properties":
                    if isinstance(instance, dict) and name in instance:
                        selected.append((instance[name], pointer + "/" + encode_pointer_token(name)))
                elif keyword == "patternProperties":
                    try:
                        pattern = re.compile(name)
                    except re.error as exc:
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "UNSUPPORTED_SCHEMA_PATTERN", str(exc))
                    if isinstance(instance, dict):
                        selected.extend((instance[key], pointer + "/" + encode_pointer_token(key))
                                        for key in sorted(instance, key=lambda x: x.encode("utf-16-be")) if pattern.search(key))
                elif keyword == "prefixItems":
                    index = int(name)
                    if isinstance(instance, list) and index < len(instance):
                        selected.append((instance[index], pointer + "/" + str(index)))
                elif keyword == "items":
                    if isinstance(instance, list):
                        first = len(parent_schema.get("prefixItems", []))
                        selected.extend((instance[index], pointer + "/" + str(index)) for index in range(first, len(instance)))
                elif keyword == "contains":
                    if isinstance(instance, list):
                        selected.extend((item, pointer + "/" + str(index)) for index, item in enumerate(instance)
                                        if self._schema_accepts(resource_root, child_schema, item))
                elif keyword == "additionalProperties":
                    if isinstance(instance, dict):
                        props, patterns = parent_schema.get("properties", {}), parent_schema.get("patternProperties", {})
                        if not isinstance(props, Mapping) or not isinstance(patterns, Mapping):
                            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ADDITIONAL_PROPERTY_DOMAIN_INVALID")
                        try:
                            compiled = [re.compile(pattern) for pattern in patterns]
                        except re.error as exc:
                            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "UNSUPPORTED_SCHEMA_PATTERN", str(exc))
                        selected.extend((instance[key], pointer + "/" + encode_pointer_token(key))
                                        for key in sorted(instance, key=lambda x: x.encode("utf-16-be"))
                                        if key not in props and not any(pattern.search(key) for pattern in compiled))
                elif keyword == "unevaluatedProperties" and isinstance(instance, dict):
                    try:
                        from jsonschema._utils import find_evaluated_property_keys_by_schema
                        prior_applicators = dict(parent_schema)
                        prior_applicators.pop("unevaluatedProperties", None)
                        evaluated = find_evaluated_property_keys_by_schema(
                            jsonschema.Draft202012Validator(resource_root), instance, prior_applicators)
                    except Exception as exc:
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "UNEVALUATED_PROPERTY_DOMAIN_UNSUPPORTED", type(exc).__name__)
                    selected.extend((instance[key], pointer + "/" + encode_pointer_token(key))
                                    for key in sorted(instance, key=lambda x: x.encode("utf-16-be")) if key not in evaluated)
                elif keyword == "unevaluatedItems" and isinstance(instance, list):
                    try:
                        from jsonschema._utils import find_evaluated_item_indexes_by_schema
                        prior_applicators = dict(parent_schema)
                        prior_applicators.pop("unevaluatedItems", None)
                        evaluated = find_evaluated_item_indexes_by_schema(
                            jsonschema.Draft202012Validator(resource_root), instance, prior_applicators)
                    except Exception as exc:
                        self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "UNEVALUATED_ITEM_DOMAIN_UNSUPPORTED", type(exc).__name__)
                    selected.extend((instance[index], pointer + "/" + str(index)) for index in range(len(instance)) if index not in evaluated)
            states = selected
        if not isinstance(current, Mapping) or "$ref" not in current:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_IS_NOT_DECLARED_REFERENCE", schema_pointer)
        return states
    def _enumerate_typed_references(self, universe: Any, registry: Any,
                                    reference_model: Any, reference_form: Any) -> list[dict[str, Any]]:
        owner_pointer, route_pointer = self._enum_contract()
        if reference_form not in ("BASE", "MEMBER"):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_FORM_SELECTOR_UNSUPPORTED", reference_form)
        if (not isinstance(universe, Mapping) or set(universe) != {"objects"} or
                not isinstance(universe.get("objects"), list) or not isinstance(registry, Mapping) or
                not isinstance(reference_model, Mapping)):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ENUMERATION_ARGUMENT_DOMAIN_INVALID")
        try:
            owner_domain = get_pointer(reference_model, owner_pointer)
            def model_pointer(specification: Any) -> str:
                if not isinstance(specification, str) or ":" not in specification:
                    raise ValueError("INVALID_MODEL_POINTER_SPECIFICATION")
                pointer = specification.split(":", 1)[1]
                if not pointer.startswith("/"):
                    raise ValueError("INVALID_MODEL_POINTER_SPECIFICATION")
                pointer_tokens(pointer)
                return pointer
            registry_owner_refs = get_pointer(reference_model, model_pointer(owner_domain["registry_owner_candidate_set_ref"]))
            schema_subject_refs = get_pointer(reference_model, model_pointer(owner_domain["schema_validation_subject_set_ref"]))
            bound_refs = get_pointer(reference_model, model_pointer(owner_domain["verified_bound_source_owner_set_ref"]))
            route_apps = get_pointer(reference_model, route_pointer)
        except (ExpressionError, KeyError, TypeError, ValueError) as exc:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ENUMERATION_MODEL_POINTER_UNRESOLVED", type(exc).__name__)
        if (not isinstance(owner_domain, Mapping) or not isinstance(registry_owner_refs, list) or
                not isinstance(schema_subject_refs, list) or not isinstance(bound_refs, list) or not isinstance(route_apps, list)):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ENUMERATION_MODEL_SHAPE_INVALID")
        role_rows = owner_domain.get("declared_kind_roles")
        membership = owner_domain.get("registry_row_membership")
        if not isinstance(role_rows, list) or not isinstance(membership, Mapping):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "OWNER_DOMAIN_DECLARATION_INVALID")
        roles: dict[str, Mapping[str, Any]] = {}
        for row in role_rows:
            if (not isinstance(row, Mapping) or not isinstance(row.get("declared_kind"), str) or
                    row["declared_kind"] in roles or not isinstance(row.get("typed_reference_owner_eligible"), bool) or
                    not isinstance(row.get("schema_validation_subject"), bool)):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "OWNER_KIND_ROLE_DECLARATION_INVALID", row)
            roles[row["declared_kind"]] = row
        rows = registry.get("objects")
        if not isinstance(rows, list) or any(not isinstance(obj, ResolvedObject) for obj in universe["objects"]):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "UNVERIFIED_ENUMERATION_INPUT")
        by_identity: dict[tuple[str, str, str], list[ResolvedObject]] = {}
        for obj in universe["objects"]:
            by_identity.setdefault(identity(obj.ref), []).append(obj)

        def base_ref(value: Any) -> dict[str, str]:
            if (not isinstance(value, Mapping) or set(value) != {"kind", "id", "version"} or
                    any(not isinstance(value.get(k), str) or not value[k] for k in ("kind", "id", "version"))):
                self._typed_reference_fail("INVALID_TYPED_REFERENCE", "OWNER_REFERENCE_INVALID", value)
            return {k: value[k] for k in ("kind", "id", "version")}

        def owner(ref_value: Any) -> ResolvedObject:
            ref = base_ref(ref_value)
            matches = by_identity.get(identity(ref), [])
            if not matches:
                self._typed_reference_fail("RESOLUTION_NOT_FOUND", "OWNER_NOT_IN_VERIFICATION_UNIVERSE", ref)
            if len(matches) != 1 or not self._same_typed_reference(matches[0].ref, ref):
                self._typed_reference_fail("RESOLUTION_AMBIGUOUS", "OWNER_IDENTITY_AMBIGUOUS", ref)
            return matches[0]

        representation = reference_model.get("representation_validation")
        ref_type = reference_model.get("reference_type")
        if not isinstance(representation, Mapping) or not isinstance(ref_type, Mapping) or ref_type.get("shape_alone_sufficient") is not False:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_ADMISSION_DECLARATION_INVALID")
        bound_definitions = self._bind_reference_definitions(universe, ref_type)
        candidate: dict[tuple[str, str, str], tuple[ResolvedObject, Mapping[str, Any], str]] = {}
        schema_subject_ids: set[tuple[str, str, str]] = set()
        for raw_ref in registry_owner_refs:
            ref = base_ref(raw_ref)
            obj = owner(ref)
            matches = [row for row in rows if isinstance(row, Mapping) and self._same_typed_reference(row.get("reference"), ref)]
            if len(matches) != 1:
                self._typed_reference_fail("RESOLUTION_NOT_FOUND" if not matches else "RESOLUTION_AMBIGUOUS",
                                           "OWNER_REGISTRY_ROW_NOT_UNIQUE", ref)
            row = matches[0]
            if row.get("status") != membership.get("status") or row.get("classification") != membership.get("classification"):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "OWNER_REGISTRY_ROW_OUTSIDE_SCOPE", ref)
            role = roles.get(ref["kind"])
            if role is None:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "OWNER_KIND_ROLE_UNDECLARED", ref)
            if role.get("schema_validation_subject"):
                schema_subject_ids.add(identity(ref))
                continue
            if not role.get("typed_reference_owner_eligible"):
                continue
            key = identity(ref)
            if key in candidate:
                self._typed_reference_fail("RESOLUTION_AMBIGUOUS", "DUPLICATE_REGISTRY_OWNER", ref)
            if not self._same_typed_reference(obj.ref, ref):
                self._typed_reference_fail("RESOLUTION_AMBIGUOUS", "OWNER_REFERENCE_MISMATCH", ref)
            candidate[key] = (obj, row, "ACTIVE_NORMATIVE_REGISTRY")
        declared_schema_ids = {identity(base_ref(ref)) for ref in schema_subject_refs}
        if schema_subject_ids != declared_schema_ids:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "SCHEMA_SUBJECT_DOMAIN_MISMATCH")

        bound: dict[tuple[str, str, str], tuple[ResolvedObject, Mapping[str, Any], str]] = {}
        for entry in bound_refs:
            if not isinstance(entry, Mapping) or entry.get("selection") != "EXACT_VERIFIED_ALLOWLIST_ENTRY":
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "BOUND_OWNER_DECLARATION_INVALID", entry)
            ref = base_ref(entry.get("reference"))
            obj = owner(ref)
            if obj.source_universe != "BOUND_SOURCE_UNIVERSE":
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "BOUND_OWNER_PROVENANCE_MISMATCH", ref)
            key = identity(ref)
            if key in bound or key in candidate:
                self._typed_reference_fail("RESOLUTION_AMBIGUOUS", "OWNER_NAMESPACE_COLLISION", ref)
            bound[key] = (obj, entry, "VERIFIED_BOUND_SOURCE")

        selected: dict[tuple[str, str, str], tuple[ResolvedObject, ResolvedObject, dict[str, str], Any, str]] = {}
        for source, is_candidate in ((candidate, True), (bound, False)):
            for key, (obj, source_row, origin) in source.items():
                producer = source_row.get("schema_ref" if is_candidate else "producer_schema_ref")
                if (not isinstance(producer, Mapping) or
                        any(not isinstance(producer.get(k), str) or not producer[k] for k in ("kind", "id", "version"))):
                    self._typed_reference_fail("UNRESOLVED_PRODUCER_SCHEMA", "ELIGIBLE_OWNER_SCHEMA_REF_MISSING", obj.ref)
                producer = dict(producer)
                role = roles.get(producer["kind"])
                if role is None or not role.get("schema_validation_subject"):
                    self._typed_reference_fail("UNRESOLVED_PRODUCER_SCHEMA", "PRODUCER_SCHEMA_KIND_UNDECLARED", producer)
                schema_matches = by_identity.get(identity(producer), [])
                schema_obj = self.schema_objects.get(identity(producer))
                if (len(schema_matches) != 1 or schema_obj is None or schema_obj is not schema_matches[0] or
                        not self._same_typed_reference(schema_obj.ref, {k: producer[k] for k in ("kind", "id", "version")})):
                    self._typed_reference_fail("UNRESOLVED_PRODUCER_SCHEMA", "PRODUCER_SCHEMA_UNRESOLVED_OR_AMBIGUOUS", producer)
                member = producer.get("member_id")
                if member is not None and (not isinstance(member, str) or not member):
                    self._typed_reference_fail("UNRESOLVED_PRODUCER_SCHEMA", "PRODUCER_SCHEMA_MEMBER_INVALID", producer)
                if member is None:
                    applied = schema_obj.content
                else:
                    if len(member_matches(schema_obj.content, member, schema_obj.registration)) != 1:
                        self._typed_reference_fail("UNRESOLVED_PRODUCER_SCHEMA", "PRODUCER_SCHEMA_MEMBER_NOT_REGISTERED", producer)
                    applied = self._member_law("UNRESOLVED_PRODUCER_SCHEMA", "MEMBER_BINDING_DECLARATION_UNAVAILABLE").locate(schema_obj.content, member)
                    if applied is REGISTRATION_CONTENT_ABSENT:
                        self._typed_reference_fail("UNRESOLVED_PRODUCER_SCHEMA", "PRODUCER_SCHEMA_MEMBER_UNRESOLVED", producer)
                if not isinstance(applied, (Mapping, bool)):
                    self._typed_reference_fail("UNRESOLVED_PRODUCER_SCHEMA", "PRODUCER_SCHEMA_NOT_SCHEMA", producer)
                # Candidate and bound contents were schema-validated in the pre-execution stages.
                # Require this selector to reuse that same resolved owner and exact schema binding.
                if not self._same_typed_reference(obj.registration.get("schema_ref"), producer):
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "OWNER_VALIDATION_PROVENANCE_MISMATCH", obj.ref)
                selected[key] = (obj, schema_obj, producer, applied, origin)

        route_inventory = reference_model.get("route_inventory")
        if not isinstance(route_inventory, Mapping):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_INVENTORY_INVALID")
        routes, summaries = route_inventory.get("declared_routes"), route_inventory.get("eligible_owners")
        if not isinstance(routes, list) or not isinstance(summaries, list):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_INVENTORY_ROWS_INVALID")
        summary_by_owner: dict[tuple[str, str, str], Mapping[str, Any]] = {}
        for row in summaries:
            if not isinstance(row, Mapping):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ELIGIBLE_OWNER_SUMMARY_INVALID", row)
            ref = base_ref(row.get("owner_ref"))
            key = identity(ref)
            if key in summary_by_owner:
                self._typed_reference_fail("RESOLUTION_AMBIGUOUS", "DUPLICATE_ELIGIBLE_OWNER_SUMMARY", ref)
            summary_by_owner[key] = row
        if set(summary_by_owner) != set(selected):
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ELIGIBLE_OWNER_INVENTORY_MISMATCH")
        for key, (_, _, producer, _, origin) in selected.items():
            summary = summary_by_owner[key]
            if (not self._same_typed_reference(summary.get("producer_schema_ref"), producer) or
                    summary.get("owner_origin") != origin):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "OWNER_SCHEMA_INVENTORY_MISMATCH", summary.get("owner_ref"))
        definitions = ref_type.get("definition_refs")
        edge_fields = reference_model.get("edge_identity")
        if not isinstance(definitions, list) or not isinstance(edge_fields, list) or not edge_fields:
            self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_DEFINITION_DOMAIN_INVALID")
        definitions_by_ref: dict[tuple[str, str, str, str], Mapping[str, Any]] = {}
        for row in definitions:
            if not isinstance(row, Mapping):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_DEFINITION_ROW_INVALID", row)
            ref = row.get("reference_definition_ref")
            key = self._ref_key(ref)
            if not all(key) or key in definitions_by_ref:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_DEFINITION_IDENTITY_INVALID", ref)
            definitions_by_ref[key] = row
        pending: dict[tuple[str, ...], tuple[tuple[bytes, ...], int, int, dict[str, Any]]] = {}
        route_counts: dict[tuple[str, str, str], int] = {key: 0 for key in selected}
        for app_index, app in enumerate(route_apps):
            if not isinstance(app, Mapping):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_APPLICATION_INVALID", app)
            owner_ref = base_ref(app.get("owner_ref"))
            key = identity(owner_ref)
            selected_row = selected.get(key)
            if selected_row is None:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_OWNER_NOT_ELIGIBLE", owner_ref)
            owner_obj, schema_obj, producer_ref, applied, origin = selected_row
            route_index = app.get("declared_route_index")
            if not isinstance(route_index, int) or isinstance(route_index, bool) or route_index < 0 or route_index >= len(routes):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "DECLARED_ROUTE_INDEX_INVALID", app)
            route = routes[route_index]
            if (not isinstance(route, Mapping) or app.get("schema_pointer") != route.get("schema_pointer") or
                    app.get("instance_path_tokens") != route.get("instance_path_tokens") or
                    not self._same_typed_reference(app.get("producer_schema_ref"), producer_ref) or
                    not self._same_typed_reference(route.get("producer_schema_ref"), producer_ref) or
                    not self._same_typed_reference(app.get("reference_definition_ref"), route.get("reference_definition_ref"))):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_APPLICATION_MISMATCH", app)
            expected_origin = summary_by_owner[key].get("owner_origin")
            if app.get("owner_origin") != expected_origin or expected_origin != origin:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_OWNER_PROVENANCE_MISMATCH", owner_ref)
            def_ref = app.get("reference_definition_ref")
            definition = definitions_by_ref.get(self._ref_key(def_ref))
            if definition is None or not self._same_typed_reference(definition.get("reference_definition_ref"), def_ref):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_DEFINITION_UNDECLARED", def_ref)
            bound_pointer = bound_definitions.get(self._ref_key(def_ref))
            if bound_pointer is None:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_DEFINITION_UNBOUND", def_ref)
            if identity(def_ref) != identity(producer_ref):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_DEFINITION_OUTSIDE_PRODUCER_DOCUMENT", def_ref)
            try:
                route_schema = get_pointer(applied, app.get("schema_pointer"))
            except ExpressionError:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_SCHEMA_POINTER_UNRESOLVED", app)
            target_pointer = self._fragment_pointer(route_schema.get("$ref")) if isinstance(route_schema, Mapping) else None
            # Identity of the bound location, never equality of schema content.
            if target_pointer is None or pointer_tokens(target_pointer) != pointer_tokens(bound_pointer):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_TARGET_NOT_DECLARED_TYPED_REFERENCE", app)
            contexts = self._route_instances(schema_obj.content, applied, owner_obj.content,
                                            app.get("schema_pointer"), app.get("instance_path_tokens"))
            try:
                route_validator = jsonschema.Draft202012Validator(schema_obj.content).evolve(schema=route_schema)
            except Exception as exc:
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "ROUTE_SCHEMA_VALIDATOR_UNAVAILABLE", type(exc).__name__)
            # The instance-tree preorder only ranks the admitted values (reference-model:/enumeration/deterministic_order).
            # max_json_traversal_depth and max_json_nodes_visited_per_value belong to DESCENDANTS (primitive-registry:/descendant_record/
            # limits, exceeded_error_class TRAVERSAL_RESOURCE_LIMIT, emission root_depth / root_visited_node_count); TRAVERSAL_RESOURCE_LIMIT
            # is not an ENUMERATE_TYPED_REFERENCES error class and no other frozen rule bounds its traversal, so the ranking walk has no
            # depth bound and no node-count bound: reference values are enumerated at any nesting depth and in any number of nodes.
            positions = {row["pointer"]: index for index, row in enumerate(
                descendants(owner_obj.content, (sys.maxsize, sys.maxsize)))}
            route_counts[key] += 1
            required = representation.get("required_keys")
            optional = representation.get("optional_keys")
            if not isinstance(required, list) or not isinstance(optional, list):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "REFERENCE_SHAPE_DECLARATION_INVALID")
            for value, instance_pointer in contexts:
                if instance_pointer not in positions or not route_validator.is_valid(value):
                    continue
                if (not isinstance(value, dict) or not set(required).issubset(value) or
                        set(value) - set(required + optional) or any(not isinstance(x, str) for x in value.values())):
                    self._typed_reference_fail("INVALID_TYPED_REFERENCE", "ADMITTED_REFERENCE_SHAPE_INVALID", value)
                member_fields = [field for field in optional if field == "member_id"]
                if member_fields and any(field in value and not value[field] for field in member_fields):
                    self._typed_reference_fail("INVALID_TYPED_REFERENCE", "ADMITTED_MEMBER_REFERENCE_INVALID", value)
                if set(value) == set(required):
                    form = "BASE"
                elif len(member_fields) == 1 and set(value) == set(required) | {member_fields[0]}:
                    form = "MEMBER"
                else:
                    self._typed_reference_fail("INVALID_TYPED_REFERENCE", "ADMITTED_REFERENCE_FORM_INVALID", value)
                if form != reference_form:
                    continue
                source_fields = {"source_kind": owner_obj.ref.get("kind"), "source_id": owner_obj.ref.get("id"),
                                 "source_version": owner_obj.ref.get("version"), "source_pointer": instance_pointer,
                                 "target_kind": value.get("kind"), "target_id": value.get("id"),
                                 "target_version": value.get("version"), "member_id_or_empty": value.get("member_id", "")}
                if any(not isinstance(field, str) or field not in source_fields for field in edge_fields):
                    self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "EDGE_IDENTITY_UNSUPPORTED", edge_fields)
                edge = tuple(source_fields[field] for field in edge_fields)
                record = {"owner_ref": dict(owner_obj.ref), "producer_schema_ref": dict(producer_ref),
                          "schema_pointer": app["schema_pointer"], "instance_pointer": instance_pointer,
                          "reference_form": form, "reference": dict(value)}
                owner_sort = tuple(part.encode("utf-16-be") for part in identity(owner_obj.ref))
                pending.setdefault(edge, (owner_sort, positions[instance_pointer], app_index, record))
        for key, summary in summary_by_owner.items():
            declared_count = summary.get("effective_route_count")
            if declared_count is not None and declared_count != route_counts.get(key):
                self._typed_reference_fail("REFERENCE_DOMAIN_UNDERDETERMINED", "OWNER_ROUTE_COUNT_MISMATCH", summary.get("owner_ref"))
        ordered = sorted(pending.values(), key=lambda row: (row[0], row[1], row[2], row[3]["schema_pointer"].encode("utf-16-be")))
        return [row[3] for row in ordered]

    def _as_json(self, value: Any) -> Any:
        if isinstance(value, ResolvedObject):
            return value.public_record()
        return value

    def _eval(self, expr: Any, env: Mapping[str, Any], scopes: tuple[dict[str, Any], ...], depth: int = 0) -> Any:
        if depth > 64:
            raise ExpressionError("RESOURCE_LIMIT")
        if not isinstance(expr, dict):
            raise ExpressionError("INVALID_EXPRESSION_NODE")
        if set(expr) == {"arg"}:
            name = expr["arg"]
            if name not in env:
                raise ExpressionError("ARGUMENT_UNBOUND", name)
            return env[name]
        if set(expr) == {"item"}:
            name = expr["item"]
            for scope in reversed(scopes):
                if name in scope:
                    return scope[name]
            raise ExpressionError("ITEM_OUT_OF_SCOPE", name)
        if set(expr) == {"literal"}:
            return expr["literal"]
        op = expr.get("op")
        if op not in self.allowed_ops:
            raise ExpressionError("UNSUPPORTED_OPERATION", op)
        ev = lambda key: self._eval(expr[key], env, scopes, depth + 1)
        if op == "RESOLVE_ONE":
            return self.resolve_one(ev("universe"), ev("reference"))
        if op == "GET":
            value = ev("value")
            pointer = expr.get("pointer")
            if not isinstance(pointer, str):
                pointer = ev("pointer")
            if isinstance(value, TypedVerificationUniverse) and pointer == "/objects":
                return [TypedResolvedJSON(obj.public_record()) for obj in value["objects"]]
            if isinstance(value, ResolvedObject):
                value = value.public_record()
            try:
                return erase_resolved_type(get_pointer(value, pointer))
            except ExpressionError as exc:
                # GET reports only the error classes declared by the primitive registry (error_behavior.error_classes):
                # a missing member or an index beyond the array is MISSING_PATH, a malformed pointer INVALID_POINTER,
                # a non-index token on an array INVALID_ARRAY_INDEX; a path through a non-container is a missing path.
                declared_classes = self.primitive_rows.get("GET", {}).get("error_behavior", {}).get("error_classes", [])
                mapped = GET_ERROR_CLASS_MAP.get(exc.error_class)
                if mapped is not None and mapped in declared_classes:
                    raise ExpressionError(mapped, exc.operand) from None
                raise
        if op == "GET_KEY":
            value, key = ev("object"), ev("key")
            if not isinstance(value, dict) or not isinstance(key, str) or key not in value:
                raise ExpressionError("KEY_NOT_FOUND", key)
            return value[key]
        if op == "JSON_EQUAL":
            return json_equal(ev("left"), ev("right"))
        if op == "SET_EQUAL_STRICT":
            left, right = ev("left"), ev("right")
            if not isinstance(left, list) or not isinstance(right, list):
                raise ExpressionError("ARRAY_TYPE_ERROR")
            return strict_set_equal(left, right)
        if op == "UNIQUE_BY":
            array = ev("array")
            if not isinstance(array, list):
                raise ExpressionError("ARRAY_TYPE_ERROR")
            pointers = expr.get("pointers")
            if not isinstance(pointers, list) or not pointers:
                raise ExpressionError("INVALID_POINTER_LIST")
            seen: set[bytes] = set()
            for row in array:
                projection = [get_pointer(row, pointer) for pointer in pointers]
                key = jcs_bytes(projection)
                if key in seen:
                    return False
                seen.add(key)
            return True
        if op in ("FILTER", "PROJECT", "ALL", "ANY"):
            array = ev("array")
            if not isinstance(array, list):
                raise ExpressionError("ARRAY_TYPE_ERROR")
            name = expr.get("as")
            if not isinstance(name, str) or any(name in s for s in scopes):
                raise ExpressionError("INVALID_LEXICAL_SCOPE")
            if op == "FILTER":
                result = []
                for item in array:
                    test = self._eval(expr["where"], env, scopes + ({name: item},), depth + 1)
                    if not isinstance(test, bool):
                        raise ExpressionError("BOOLEAN_TYPE_ERROR")
                    if test:
                        result.append(item)
                return result
            if op == "PROJECT":
                fields = expr.get("fields")
                if not isinstance(fields, dict) or not fields:
                    raise ExpressionError("INVALID_PROJECTION")
                result = []
                for item in array:
                    scope = scopes + ({name: item},)
                    result.append({k: erase_resolved_type(self._eval(v, env, scope, depth + 1)) for k, v in fields.items()})
                return result
            if op == "ALL":
                for item in array:
                    test = self._eval(expr["where"], env, scopes + ({name: item},), depth + 1)
                    if not isinstance(test, bool):
                        raise ExpressionError("BOOLEAN_TYPE_ERROR")
                    if not test:
                        return False
                return True
            for item in array:
                test = self._eval(expr["where"], env, scopes + ({name: item},), depth + 1)
                if not isinstance(test, bool):
                    raise ExpressionError("BOOLEAN_TYPE_ERROR")
                if test:
                    return True
            return False
        if op == "COUNT":
            array = ev("array")
            if not isinstance(array, list):
                raise ExpressionError("ARRAY_TYPE_ERROR")
            return len(array)
        if op == "NOT":
            value = ev("value")
            if not isinstance(value, bool):
                raise ExpressionError("BOOLEAN_TYPE_ERROR")
            return not value
        if op == "NUMERIC_COMPARE":
            return compare_numbers(ev("left"), ev("right"), expr.get("comparator"))
        if op == "RFC3339_COMPARE":
            left, right = timestamp_seconds(ev("left")), timestamp_seconds(ev("right"))
            return compare_numbers(left, right, expr.get("comparator"))
        if op == "DURATION_SECONDS":
            return timestamp_seconds(ev("end")) - timestamp_seconds(ev("start"))
        if op == "SCHEMA_VALIDATE":
            schema_value, instance_value = ev("schema"), ev("instance")
            try:
                return schema_is_valid(schema_value, instance_value, expr.get("mode"))
            except ExpressionError as exc:
                # SCHEMA_VALIDATE reports only the error classes declared by the primitive registry (error_behavior.error_classes).
                declared_classes = self.primitive_rows.get("SCHEMA_VALIDATE", {}).get("error_behavior", {}).get("error_classes", [])
                mapped = SCHEMA_VALIDATE_ERROR_CLASS_MAP.get(exc.error_class)
                if mapped is not None and mapped in declared_classes:
                    raise ExpressionError(mapped, exc.operand) from None
                raise
        if op == "DIGEST_VERIFY":
            value = ev("value")
            typed_value = isinstance(value, (ResolvedObject, TypedResolvedJSON))
            public_value = value.public_record() if isinstance(value, ResolvedObject) else value
            is_resolved = (typed_value and self.resolved_object_validator is not None and isinstance(public_value, dict)
                           and next(self.resolved_object_validator.iter_errors(public_value), None) is None)
            def declared_raw_bytes() -> bytes:
                if not is_resolved:
                    raise ExpressionError("RAW_BYTES_UNAVAILABLE")
                encoded = public_value["raw_content_base64"]
                try:
                    raw = base64.b64decode(encoded, validate=True)
                except (ValueError, binascii.Error) as exc:
                    raise ExpressionError("RAW_BYTES_UNAVAILABLE") from exc
                if base64.b64encode(raw).decode("ascii") != encoded:
                    raise ExpressionError("RAW_BYTES_UNAVAILABLE")
                return raw
            expected = ev("expected")
            algorithm = ev("algorithm")
            serialization = ev("serialization")
            excluded = ev("excluded_pointers")
            if not isinstance(expected, str) or not isinstance(algorithm, str) or not isinstance(serialization, str):
                raise ExpressionError("INVALID_DIGEST_MODE")
            if not isinstance(excluded, list) or not all(isinstance(x, str) for x in excluded):
                raise ExpressionError("INVALID_DIGEST_EXCLUSIONS")
            if serialization == "RAW_BYTES":
                if algorithm != "SHA-256" or excluded:
                    raise ExpressionError("INVALID_ALGORITHM_SERIALIZATION_PAIR")
                actual = sha256(declared_raw_bytes())
            elif serialization == "GIT_BLOB_OBJECT":
                if algorithm != "SHA-1" or excluded:
                    raise ExpressionError("INVALID_ALGORITHM_SERIALIZATION_PAIR")
                actual = git_blob_id(declared_raw_bytes())
            elif serialization == "RFC8785_JCS" and algorithm == "SHA-256":
                actual = semantic_digest(public_value["content"] if is_resolved else public_value, excluded)
            else:
                raise ExpressionError("INVALID_DIGEST_MODE")
            return actual == expected
        if op == "ENUMERATE_TYPED_REFERENCES":
            return self._enumerate_typed_references(ev("universe"), ev("registry"),
                                                    ev("reference_model"), ev("reference_form"))
        if op == "DESCENDANTS":
            return descendants(ev("value"))
        raise ExpressionError("UNIMPLEMENTED_PRIMITIVE", op)

    def execute(self, procedure: Mapping[str, Any], arguments: Mapping[str, Any],
                bound_identities: Mapping[str, Mapping[str, str]], trust: Mapping[str, Any]) -> dict[str, Any]:
        """Run one procedure; failures use the registered result contract that governs them."""
        self.assertions_evaluated = 0
        argument_names = {arg["name"] for arg in procedure.get("arguments", [])}
        if set(arguments) != argument_names:
            owner = self.witness_law_owner
            raise VerificationError("SCHEMA_INVALID_BOUND_OBJECT", {"argument": "metacontract",
                "object_role": "procedure_binding", "schema_ref": owner.registration["schema_ref"]["id"],
                "instance_pointer": "/procedure_bindings", "failure_kind": "SOURCE_ELIGIBILITY",
                "diagnostic": "ARGUMENT_BINDING_NOT_EXACT",
                "bound_identity": ident_record(owner.ref["kind"], owner.ref["id"], owner.ref["version"])})
        trust_procedure = procedure.get("result", {}).get("type") == "TRUST_RESULT"
        for index, assertion in enumerate(procedure.get("assertions", [])):
            self.assertions_evaluated += 1
            try:
                condition = self._eval(assertion["condition"], arguments, ())
                if not isinstance(condition, bool):
                    raise ExpressionError("ASSERTION_TYPE_ERROR")
            except ExpressionError as exc:
                if trust_procedure:
                    return trust_failure(assertion.get("failure_code", ""), trust, self.witness_law_owner)
                dedicated = self.reference_resolution_failure(procedure, assertion, arguments, exc)
                if dedicated is not None:
                    return dedicated
                return self._projected(procedure, arguments, "FAIL", self._failed(
                    procedure, index, assertion, bound_identities, error_class=exc.error_class, actual=exc.operand))
            if not condition:
                if trust_procedure:
                    return trust_failure(assertion.get("failure_code", ""), trust, self.witness_law_owner)
                try:
                    witness_value = self._eval(assertion["witness"], arguments, ())
                except ExpressionError as exc:
                    witness_value = {"error_class": exc.error_class, "operand": exc.operand}
                return self._projected(procedure, arguments, "FAIL", self._failed(
                    procedure, index, assertion, bound_identities, expected=True, actual=witness_value, condition="FALSE"))
        if trust_procedure:
            return {"status": "PASS", "code": "EXPECTED_PACKAGE_VERIFIED", "witness": trust["witness"]}
        return self._projected(procedure, arguments, "PASS", {"status": "PASS", "procedure_id": procedure["procedure_id"],
                                                              "witness": {"assertions_evaluated": self.assertions_evaluated}})

    @staticmethod
    def _projected(procedure: Mapping[str, Any], arguments: Mapping[str, Any], status: str,
                   result: dict[str, Any]) -> dict[str, Any]:
        # A declared result projection maps both PASS and FAIL through the bound outcome map.
        projection = procedure.get("result", {}).get("result_projection")
        if projection:
            map_value = arguments[projection["argument"]]
            pointer = "/" + "/".join(encode_pointer_token(x) for x in projection["pointer_tokens"])
            result["result"] = get_pointer(map_value, pointer)[status]
        return result

    def _failed(self, procedure: Mapping[str, Any], index: int, assertion: Mapping[str, Any],
                bound_identities: Mapping[str, Mapping[str, str]], expected: Any = None, actual: Any = None,
                error_class: str | None = None, condition: str = "EVALUATION_ERROR") -> dict[str, Any]:
        owner = self.witness_law_owner
        law = generic_witness_law(self.metacontract, owner)
        node_path = canonical_node_path(law, owner, self.procedure_positions[procedure.get("procedure_id", "")], index)
        operand_rows = []
        for name, pointer in declared_witness_operands(self.metacontract, assertion.get("witness"), owner):
            operand_rows.append({"argument": name, "pointer": pointer,
                                 "identity": operand_identity(law, owner, procedure, name, bound_identities)})
        witness = {"operands": operand_rows, "condition": condition}
        if expected is not None:
            witness["expected"] = expected
        if actual is not None:
            witness["actual"] = actual
        if error_class:
            witness["error_class"] = error_class
        return {"status": "FAIL", "procedure_id": procedure.get("procedure_id", ""),
                "node_path": node_path, "assertion_id": assertion.get("assertion_id", ""),
                "code": assertion.get("failure_code", "INVALID_ASSERTION"), "witness": witness}

    def reference_resolution_failure(self, procedure: Mapping[str, Any], assertion: Mapping[str, Any],
                                     arguments: Mapping[str, Any], exc: ExpressionError) -> dict[str, Any] | None:
        """metacontract:/result_contracts/reference_resolution_failure, or None when its trigger does not hold.

        The failing occurrence is re-derived from the declared first-failure order: the first
        enumerated element whose RESOLVE_ONE failure kind is RESOLUTION_NOT_FOUND.
        """
        contract = self.metacontract.get("result_contracts", {}).get("reference_resolution_failure", {})
        if (procedure.get("procedure_id") != contract.get("procedure_id")
                or assertion.get("assertion_id") not in contract.get("assertion_ids", [])
                or exc.error_class != contract.get("failure_kind")):
            return None
        construction = contract.get("witness_construction", {})
        order = construction.get("first_failure_order", {})
        if (construction.get("trigger") != "RESOLVE_ONE_FAILURE_KIND_EQUALS_RESOLUTION_NOT_FOUND_FOR_AN_ENUMERATED_TYPED_REFERENCE"
                or order.get("occurrence_selection") != "FIRST_ENUMERATED_ARRAY_ELEMENT_WHOSE_RESOLVE_ONE_FAILURE_KIND_IS_RESOLUTION_NOT_FOUND"
                or order.get("evaluation") != "SHORT_CIRCUIT_ON_FIRST_RESOLUTION_NOT_FOUND"):
            raise law_failure(self.witness_law_owner, "/result_contracts/reference_resolution_failure/witness_construction",
                              "UNSUPPORTED_REFERENCE_RESOLUTION_FAILURE_CONTRACT")
        condition = assertion.get("condition", {})
        enumeration = condition.get("array") if isinstance(condition, Mapping) else None
        if not isinstance(enumeration, Mapping) or enumeration.get("op") != "ENUMERATE_TYPED_REFERENCES":
            return None
        try:
            occurrences = self._eval(enumeration, arguments, ())
            universe = self._eval(enumeration["universe"], arguments, ())
        except ExpressionError:
            return None
        failing = None
        for occurrence in occurrences:
            try:
                self.resolve_one(universe, occurrence.get("reference"))
            except ExpressionError as probe:
                if probe.error_class == "RESOLUTION_NOT_FOUND":
                    failing = occurrence
                break
        if failing is None:
            return None
        provenance = construction.get("field_provenance", {})
        classification = construction.get("owner_classification", {})
        owner = jcs_bytes(failing.get("owner_ref"))
        model = arguments.get("reference_model") or {}
        registry = arguments.get("registry") or {}
        bound_owners = {jcs_bytes(row.get("reference")) for row in model.get("bound_source_references", []) if isinstance(row, Mapping)}
        candidate_owners = {jcs_bytes(row.get("reference")) for row in registry.get("objects", [])
                            if isinstance(row, Mapping) and row.get("status") == "ACTIVE" and row.get("classification") == "NORMATIVE"}
        if (classification.get("verified_bound_source_owner") ==
                "FIRST_FAILURE.owner_ref_JSON_EQUAL_TO_ANY_reference_model.bound_source_references[*].reference_BY_TYPED_REFERENCE_IDENTITY"
                and owner in bound_owners):
            owner_class = "verified_bound_source_owner"
        elif (classification.get("candidate_registry_owner") ==
                "FIRST_FAILURE.owner_ref_JSON_EQUAL_TO_REFERENCE_OF_AN_EXACT_ACTIVE_NORMATIVE_REGISTRY_ROW"
                and owner in candidate_owners):
            owner_class = "candidate_registry_owner"
        else:
            raise law_failure(self.witness_law_owner, "/result_contracts/reference_resolution_failure/witness_construction/owner_classification",
                              "RESOLUTION_FAILURE_OWNER_UNCLASSIFIED")
        witness = {"argument": provenance["argument"][owner_class], "object_role": provenance["object_role"][owner_class],
                   "schema_ref": failing.get("producer_schema_ref"), "instance_pointer": failing.get("instance_pointer"),
                   "failure_kind": "RESOLUTION_NOT_FOUND", "diagnostic": provenance.get("diagnostic"),
                   "bound_identity": failing.get("reference")}
        if list(witness) != contract.get("witness_fields"):
            raise law_failure(self.witness_law_owner, "/result_contracts/reference_resolution_failure/witness_fields",
                              "WITNESS_FIELD_SET_MISMATCH")
        return {"status": "FAIL", "stage": contract["stage"], "code": contract["code"],
                "procedure_id": procedure["procedure_id"], "assertion_id": assertion["assertion_id"],
                "failure_kind": contract["failure_kind"], "witness": witness,
                "diagnostics": {"selected_occurrence_reference_form": failing.get("reference_form")}}


def trust_failure(code: str, gate: Mapping[str, Any], owner: ResolvedObject) -> dict[str, Any]:
    """A TRUST_RESULT procedure failing after a passing trust gate, in its registered FAIL branch shape."""
    expected, actual = gate["witness"]["expected"], gate["witness"]["actual"]
    if code == "FOREIGN_PACKAGE_IDENTITY":
        return {"status": "FAIL", "code": code, "witness": {"stage": "IDENTITY_COMPARISON",
                "expected": {"id": expected["id"], "version": expected["version"]},
                "actual": {"id": actual["id"], "version": actual["version"]}}}
    if code == "TRUSTED_IDENTITY_MISMATCH":
        return {"status": "FAIL", "code": code, "witness": {"stage": "DIGEST_COMPARISON",
                "expected": dict(expected), "actual": dict(actual)}}
    raise law_failure(owner, "/result_contracts/trust_result", "TRUST_PROCEDURE_FAILURE_HAS_NO_REGISTERED_WITNESS")


def law_failure(owner: ResolvedObject, instance_pointer: str, diagnostic: str) -> VerificationError:
    """The generic witness law fails closed at its declared owner, the metacontract."""
    return VerificationError("SCHEMA_INVALID_BOUND_OBJECT", {"argument": "metacontract",
        "object_role": "generic_failure_witness", "schema_ref": owner.registration["schema_ref"]["id"],
        "instance_pointer": instance_pointer, "failure_kind": "TYPE", "diagnostic": diagnostic,
        "bound_identity": ident_record(owner.ref["kind"], owner.ref["id"], owner.ref["version"])})


def generic_witness_law(metacontract: Mapping[str, Any], owner: ResolvedObject) -> Mapping[str, Any]:
    law = metacontract.get("failure_semantics", {}).get("generic_failure_witness")
    operands = law.get("operands", {}) if isinstance(law, Mapping) else {}
    if (not isinstance(law, Mapping) or law.get("law_id") != "GENERIC_PROCEDURE_ASSERTION_FAILURE_WITNESS"
            or operands.get("source_expression") != "THE_FAILING_ASSERTION_DECLARED_WITNESS_EXPRESSION_ONLY"
            or operands.get("condition_expression_contributes") is not False
            or operands.get("union_with_condition_operands") is not False
            or operands.get("order") != "FIRST_OCCURRENCE_PREORDER_OF_THE_DECLARED_WITNESS_EXPRESSION"
            or operands.get("deduplication_key") != ["argument", "pointer"]
            or operands.get("deduplication") != "KEEP_FIRST_OCCURRENCE"
            or operands.get("post_deduplication_sort") is not False
            or operands.get("bare_terminal_pointer") != ""
            or operands.get("non_literal_get_pointer") != "FAIL_CLOSED"
            or operands.get("missing_identity") != "FAIL_CLOSED"
            or operands.get("intermediate_get_operands") is not False
            or not str(operands.get("path_construction", "")).startswith("MAXIMAL_ENCLOSING_LITERAL_GET_CHAIN_ROOTED_AT_THE_TERMINAL")
            or operands.get("preorder_child_order") != ("DECLARED_OPERATOR_SLOT_ORDER_OF_metacontract:/runtime_representation/"
                                                        "static_type_calculus/operator_rules/operators;"
                                                        "NAMED_EXPRESSION_MAP_FIELD_NAMES_UTF16_CODE_UNIT_ASCENDING")
            or operands.get("record_fields") != ["argument", "pointer", "identity"]
            or law.get("node_path", {}).get("procedure_relative_paths") != "FORBIDDEN"):
        raise law_failure(owner, "/failure_semantics/generic_failure_witness", "UNSUPPORTED_GENERIC_FAILURE_WITNESS_LAW")
    return law


def canonical_node_path(law: Mapping[str, Any], owner: ResolvedObject, procedure_position: int, assertion_position: int) -> str:
    parts = []
    for token in law["node_path"].get("reference_tokens", []):
        kind = token.get("source")
        if kind == "LITERAL":
            parts.append(encode_pointer_token(token["value"]))
        elif kind == "PROCEDURE_INDEX":
            parts.append(str(procedure_position))
        elif kind == "ASSERTION_INDEX":
            parts.append(str(assertion_position))
        else:
            raise law_failure(owner, "/failure_semantics/generic_failure_witness/node_path/reference_tokens", "UNSUPPORTED_NODE_PATH_TOKEN")
    return "".join("/" + part for part in parts)


def declared_witness_operands(metacontract: Mapping[str, Any], witness: Any, owner: ResolvedObject) -> list[tuple[str, str]]:
    """Argument terminals of the declared witness: first-occurrence preorder, (argument, pointer) de-duplicated."""
    operator_slots = metacontract["runtime_representation"]["static_type_calculus"]["operator_rules"]["operators"]

    def rooted(node: Any) -> tuple[str, list[str]] | None:
        # A GET whose value chain bottoms out at an argument terminal names one composed pointer.
        if not (isinstance(node, Mapping) and node.get("op") == "GET"):
            return None
        pointer = node.get("pointer")
        if not isinstance(pointer, str):
            raise law_failure(owner, "/failure_semantics/generic_failure_witness/operands/non_literal_get_pointer", "NON_LITERAL_WITNESS_POINTER")
        inner = node.get("value")
        if isinstance(inner, Mapping) and set(inner) == {"arg"}:
            return inner["arg"], pointer_tokens(pointer)
        below = rooted(inner)
        return None if below is None else (below[0], below[1] + pointer_tokens(pointer))

    found: list[tuple[str, str]] = []
    stack: list[Any] = [witness]
    while stack:
        node = stack.pop()
        if not isinstance(node, Mapping):
            continue
        if set(node) == {"arg"}:
            pair = (node["arg"], "")
        else:
            chain = rooted(node)
            pair = None if chain is None else (chain[0], "".join("/" + encode_pointer_token(t) for t in chain[1]))
        if pair is not None:
            if pair not in found:
                found.append(pair)
            continue
        children: list[Any] = []
        for slot_name, slot_kind in operator_slots.get(node.get("op"), {}).get("slots", []):
            child = node.get(slot_name)
            if slot_kind == "EXPRESSION":
                children.append(child)
            elif slot_kind == "NAMED_EXPRESSION_MAP" and isinstance(child, Mapping):
                children.extend(child[key] for key in sorted(child, key=lambda text: text.encode("utf-16-be")))
        stack.extend(reversed(children))
    return found


def operand_identity(law: Mapping[str, Any], owner: ResolvedObject, procedure: Mapping[str, Any], name: str,
                     bound_identities: Mapping[str, Mapping[str, str]]) -> dict[str, str]:
    spec = next((arg for arg in procedure.get("arguments", []) if arg.get("name") == name), None)
    if spec is not None and spec.get("origin") == "RULE_BINDING" and name in bound_identities:
        return dict(bound_identities[name])
    for row in law.get("operand_only_identities", []):
        if (spec is not None and row.get("argument") == name and row.get("argument_origin") == spec.get("origin")
                and row.get("argument_type") == spec.get("type")):
            return dict(row["identity"])
    raise law_failure(owner, "/failure_semantics/generic_failure_witness/operand_only_identities", "WITNESS_OPERAND_IDENTITY_UNDECLARED")



def bound_argument_identities(procedure: Mapping[str, Any], refs: Mapping[str, Any],
                              candidate_by_ref: Mapping[tuple[str, str, str], ResolvedObject],
                              bound_by_ref: Mapping[tuple[str, str, str], ResolvedObject]) -> dict[str, dict[str, str]]:
    """kind/id/version of the object each RULE_BINDING argument is bound to."""
    out: dict[str, dict[str, str]] = {}
    for arg in procedure.get("arguments", []):
        if arg.get("origin") != "RULE_BINDING" or not isinstance(refs.get(arg.get("name")), dict):
            continue
        pool = bound_by_ref if arg.get("source_constraint", {}).get("universe") == "BOUND_SOURCE_UNIVERSE" else candidate_by_ref
        obj = pool.get(identity(refs[arg["name"]]))
        if obj is not None:
            out[arg["name"]] = ident_record(obj.ref["kind"], obj.ref["id"], obj.ref["version"])
    return out



def load_schema_ref(schema_objects: Mapping[tuple[str, str, str], ResolvedObject], ref: Mapping[str, Any],
                    law: Any = None) -> Any:
    obj = schema_objects.get(identity(ref))
    if obj is None or obj.registration.get("kind") != "SCHEMA":
        raise ExpressionError("SCHEMA_REFERENCE_UNRESOLVED", ref)
    member = ref.get("member_id")
    if member is None:
        return obj.content
    # Registered membership is decided first (exactly one equal registered
    # member); only then is the member located through the declared binding.
    # There is no fallback to an unregistered local definition.
    if len(member_matches(obj.content, member, obj.registration)) != 1:
        raise ExpressionError("MEMBER_NOT_FOUND", ref)
    if (not isinstance(law, SchemaMemberLaw) or law.registry_kind != obj.registration.get("kind")
            or law.locate(obj.content, member) is REGISTRATION_CONTENT_ABSENT):
        raise ExpressionError("MEMBER_NOT_FOUND", ref)
    return law.member_schema(obj.content, member)



def external_trust_record(declaration: Mapping[str, Any], trust: Mapping[str, Any]) -> dict[str, Any]:
    witness = trust.get("witness") if isinstance(trust, Mapping) else None
    expected = witness.get("expected") if isinstance(witness, Mapping) else None
    record = {
        "expected_package_id": expected.get("id") if isinstance(expected, Mapping) else None,
        "expected_package_version": expected.get("version") if isinstance(expected, Mapping) else None,
        "expected_package_digest": expected.get("digest") if isinstance(expected, Mapping) else None,
        "digest_mode": {"algorithm": "SHA-256", "serialization": "RFC8785_JCS",
                        "excluded_pointers": ["/current_candidate_integrity/digest"]},
    }
    return record



REGISTRATION_SCHEMA_ID = REGISTRATION["witness_contract"]["schema_ref"]  # committed registration witness contract
REGISTRATION_OBJECT_ROLE = REGISTRATION["witness_contract"]["object_role"]

def registration_row_identity(row: Any) -> tuple[str, str, str] | None:
    if not isinstance(row, Mapping):
        return None
    values = (row.get("kind"), row.get("id"), row.get("version"))
    if not all(isinstance(value, str) and value for value in values):
        return None
    return (values[0], values[1], values[2])



REGISTRATION_SEMANTIC_ROLE = "SEMANTIC_REGISTRATION"
REGISTRATION_SEMANTIC_STAGE = "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS"
REGISTRATION_INSTANCE_SCOPE = "FULL_REGISTRY_ALL_ROWS"
REGISTRATION_FAILURE_STAGE = "PRE_EXECUTION"
REGISTRATION_FAILURE_CODE = "SCHEMA_INVALID_BOUND_OBJECT"
REGISTRATION_POINTER_PREFIX = "/objects/<row_index>"
REGISTRATION_ROW_SCOPES = ("ALL_ROWS", "NON_SCHEMA_ROWS_ONLY", "SCHEMA_ROWS_ONLY")
REGISTRATION_RULE_SCOPES = {
    "SCHEMA_KIND_MUST_NOT_DECLARE_ROW_SCHEMA_REF": ("ALL_ROWS",),
    "STATUS_IN_REGISTRY_STATUS_VOCABULARY": ("ALL_ROWS",),
    "CLASSIFICATION_IN_REGISTRY_CLASSIFICATION_VOCABULARY": ("ALL_ROWS",),
    "REGISTRATION_SCHEMA_REF_RESOLVES_TO_REGISTERED_SCHEMA_ROW": ("ALL_ROWS",),
    "ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY": ("ALL_ROWS",),
    "NON_SCHEMA_ROW_CONTENT_DECLARED_IDENTITY_EQUALS_ROW_REGISTRY_IDENTITY": ("NON_SCHEMA_ROWS_ONLY",),
    "SCHEMA_DOCUMENT_VERSION_EQUALS_ROW_VERSION": ("SCHEMA_ROWS_ONLY",),
    "SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID": ("SCHEMA_ROWS_ONLY",),
    "SCHEMA_ROW_REGISTERED_MEMBERS_BIND_TO_ROOT_DEFS_ENTRIES": ("SCHEMA_ROWS_ONLY",),
}
MEMBER_BINDING_RULE_ID = "SCHEMA_ROW_REGISTERED_MEMBERS_BIND_TO_ROOT_DEFS_ENTRIES"
REGISTRATION_CONDITION_MARKERS = {
    "SCHEMA_KIND_MUST_NOT_DECLARE_ROW_SCHEMA_REF": ("ROW_KIND_SCHEMA", "ROW_SCHEMA_REF_PRESENT"),
    "STATUS_IN_REGISTRY_STATUS_VOCABULARY": ("STATUS_NOT_IN_REGISTRY_STATUS_VOCABULARY",),
    "CLASSIFICATION_IN_REGISTRY_CLASSIFICATION_VOCABULARY": ("CLASSIFICATION_NOT_IN_REGISTRY_CLASSIFICATION_VOCABULARY",),
    "REGISTRATION_SCHEMA_REF_RESOLVES_TO_REGISTERED_SCHEMA_ROW": ("DOES_NOT_RESOLVE_TO_A_REGISTERED_SCHEMA_KIND_ROW",),
    "ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY": ("REFERENCE_NOT_EQUAL_TO_ROW_KIND_ID_VERSION_TRIPLE",),
    "NON_SCHEMA_ROW_CONTENT_DECLARED_IDENTITY_EQUALS_ROW_REGISTRY_IDENTITY": ("ROW_KIND_ID_VERSION_NOT_EQUAL_TO_THE_IDENTITY_DECLARED_BY_THE_REGISTERED_CONTENT",),
    "SCHEMA_DOCUMENT_VERSION_EQUALS_ROW_VERSION": ("SCHEMA_DOCUMENT_VERSION_NOT_EQUAL_TO_ROW_VERSION",),
    "SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID": ("JSON_STRING_VALUE_OF_THE_SLASH_DOLLAR_ID_MEMBER",),
    "SCHEMA_ROW_REGISTERED_MEMBERS_BIND_TO_ROOT_DEFS_ENTRIES": ("A_REGISTERED_MEMBER_ID_IS_NOT_THE_EXACT_NAME_OF_A_ROOT_LEVEL_DEFS_ENTRY",),
}
REGISTRATION_UNCHANGED_RELATIONS = ("UNCHANGED_FROM_THE_PRIOR_COMBINED_RULE_FOR_NON_SCHEMA_ROWS_ONLY",)
REGISTRATION_WITNESS_FIELDS = ("argument", "object_role", "schema_ref", "instance_pointer",
                               "failure_kind", "diagnostic", "bound_identity")
REGISTRATION_BOUND_IDENTITY_TOKEN = "ROW_KIND_ID_VERSION_TRIPLE_WHEN_READABLE_ELSE_NULL"
GLOBAL_UNIQUENESS_ROLE = "GLOBAL_UNIQUENESS"
GLOBAL_UNIQUENESS_STAGE = "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY"
GLOBAL_UNIQUENESS_PROPERTY = "REGISTRY_OBJECT_IDENTITY_UNIQUENESS"
GLOBAL_UNIQUENESS_POINTER_TEMPLATE = "/objects/<second_occurrence_index>"
GLOBAL_UNIQUENESS_RESULT_CONTRACT_REF = "metacontract:/result_contracts/pre_execution_result"
GLOBAL_UNIQUENESS_SELECTION_TOKENS = {
    "array_order_source": "SOURCE_/objects_ARRAY_ORDER_NORMATIVE",
    "second_occurrence_scan": "ASCENDING_INDEX_J_MINIMAL_MATCHING_PRIOR_EXISTS",
    "first_occurrence_selection": "EARLIEST_PRIOR_MATCHING_ROW_MINIMAL_I_LESS_THAN_J",
    "decision_source": "DECLARED_SCAN_ORDER_ONLY_MAP_OR_SET_ITERATION_ORDER_FORBIDDEN",
}


class _RegistrationSentinel:
    __slots__ = ("token",)

    def __init__(self, token: str) -> None:
        self.token = token

    def __repr__(self) -> str:
        return self.token


REGISTRATION_CONTENT_ABSENT = _RegistrationSentinel("REGISTRATION_CONTENT_ABSENT")
REGISTRATION_CONTENT_UNREADABLE = _RegistrationSentinel("REGISTRATION_CONTENT_UNREADABLE")

# ---------------------------------------------------------------------------
# ACCORD-02E4R5R4 declaration-driven registration conformance (independent).
#
# The stage, the ordered comparisons, their instance pointers, their
# diagnostics, the governed failure kind and the exact witness members are read
# from metacontract:/registration through registration_declarations(); any
# declaration this evaluator does not implement fails closed through
# registration_unsupported(). Comparisons are derived from the declared member
# names (registry_identity_members, schema_document_identity_members,
# schema_content_id_member) instead of an evaluator-side member table.
# ---------------------------------------------------------------------------
def registration_unsupported() -> ModelGap:
    # An unsupported registration declaration is an implementation gap, never a registered result (PE-22 owns
    # every committed-declaration difference before any registration stage runs).
    return ModelGap("REGISTRATION_DECLARATION_NOT_IMPLEMENTED")


def registration_pointer_tokens(pointer: Any) -> list[str] | None:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return None
    return [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]


def registration_pointer_value(document: Any, tokens: Sequence[str]) -> Any:
    value = document
    for token in tokens:
        if not isinstance(value, Mapping) or token not in value:
            return REGISTRATION_CONTENT_ABSENT
        value = value[token]
    return value


MEMBER_LAW_TOKENS = {
    "binding_id": "EXPLICIT_REGISTERED_SCHEMA_MEMBER",
    "member_id_domain": "NONEMPTY_JSON_STRING",
    "member_id_to_definition_name": "EXACT_JSON_STRING_EQUALITY",
    "absent_members": "EMPTY_REGISTERED_MEMBER_SET",
    "unregistered_local_definitions": "SCHEMA_LANGUAGE_INTERNALS_NOT_ACCORD_ADDRESSABLE",
    "raw_local_defs_lookup_without_registration": "FORBIDDEN",
    "member_inference_from_names_suffixes_or_patterns": "FORBIDDEN",
}
MEMBER_LAW_CONSTRUCTION_TOKENS = {
    "pointer_standard": "RFC6901",
    "pointer_base": "ROOT_OF_THE_DEFINITION_DOCUMENT",
    "token_escaping": "RFC6901_ENCODE_TILDE_AS_TILDE0_THEN_SLASH_AS_TILDE1",
}
MEMBER_LAW_SELECTION_STEPS = (
    "RESOLVE_THE_EXACT_OWNER_KIND_ID_VERSION_IN_THE_EXPLICIT_VERIFICATION_UNIVERSE",
    "IF_member_id_IS_ABSENT_RETURN_THE_BASE_RESOLVED_OBJECT",
    "REQUIRE_EXACTLY_ONE_EQUAL_STRING_IN_THE_RESOLVED_OBJECT_REGISTERED_members",
    "BIND_THE_SELECTED_MEMBER_TO_THE_CONSTRUCTED_ROOT_DEFS_POINTER_IN_THE_SAME_RESOLVED_CONTENT",
)


class SchemaMemberLaw:
    """The explicit registered SCHEMA member binding declared by the candidate metacontract.

    A registered member_id is located by assembling the declared reference-token
    sequence (literal tokens and the member_id itself), encoding each token with
    RFC6901 escaping, and walking that pointer from the owner document root.
    This object never decides membership; callers first require exactly one
    equal registered member.
    """

    __slots__ = ("reference", "registry_kind", "steps")

    def __init__(self, reference: str, registry_kind: str, steps: tuple[Any, ...]) -> None:
        self.reference = reference
        self.registry_kind = registry_kind
        self.steps = steps

    def _tokens(self, member_id: str) -> list[str]:
        return [member_id if step is None else step for step in self.steps]

    def pointer_for(self, member_id: str) -> str:
        return "".join("/" + encode_pointer_token(token) for token in self._tokens(member_id))

    def locate(self, document: Any, member_id: Any) -> Any:
        if not isinstance(member_id, str) or not member_id:
            return REGISTRATION_CONTENT_ABSENT
        return registration_pointer_value(document, self._tokens(member_id))

    def member_schema(self, document: Any, member_id: str) -> Any:
        # Validation schema for the bound member: a $ref to the constructed
        # pointer inside the parent document's declared container, so local
        # fragment references of the member keep their parent context.
        container = self.steps[0]
        return {"$schema": document.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
                "$ref": "#" + self.pointer_for(member_id), container: document[container]}


def declared_member_law(metacontract: Any, reference: Any) -> SchemaMemberLaw:
    """Parse the binding named by a 'metacontract:<pointer>' reference; ValueError when unsupported."""
    prefix = "metacontract:"
    if not isinstance(metacontract, Mapping) or not isinstance(reference, str) or not reference.startswith(prefix):
        raise ValueError("MEMBER_BINDING_REFERENCE_UNSUPPORTED")
    tokens = registration_pointer_tokens(reference[len(prefix):])
    declaration = registration_pointer_value(metacontract, tokens) if tokens is not None else REGISTRATION_CONTENT_ABSENT
    if not isinstance(declaration, Mapping):
        raise ValueError("MEMBER_BINDING_DECLARATION_ABSENT")
    if any(declaration.get(key) != value for key, value in MEMBER_LAW_TOKENS.items()):
        raise ValueError("MEMBER_BINDING_TOKEN_UNSUPPORTED")
    if declaration.get("nested_definitions_eligible") is not False or declaration.get("non_defs_locations_eligible") is not False:
        raise ValueError("MEMBER_BINDING_LOCATION_SCOPE_UNSUPPORTED")
    if tuple(declaration.get("selection_order") or ()) != MEMBER_LAW_SELECTION_STEPS:
        raise ValueError("MEMBER_BINDING_SELECTION_ORDER_UNSUPPORTED")
    registry_kind = declaration.get("applies_to_registry_kind")
    construction = declaration.get("definition_pointer_construction")
    if not isinstance(registry_kind, str) or not registry_kind or not isinstance(construction, Mapping):
        raise ValueError("MEMBER_BINDING_CONSTRUCTION_ABSENT")
    if any(construction.get(key) != value for key, value in MEMBER_LAW_CONSTRUCTION_TOKENS.items()):
        raise ValueError("MEMBER_BINDING_CONSTRUCTION_UNSUPPORTED")
    steps: list[Any] = []
    for token in construction.get("reference_tokens") or []:
        if token == {"source": "MEMBER_ID"}:
            steps.append(None)
        elif (isinstance(token, Mapping) and set(token) == {"source", "value"} and token.get("source") == "LITERAL"
              and isinstance(token.get("value"), str) and token["value"]):
            steps.append(token["value"])
        else:
            raise ValueError("MEMBER_BINDING_TOKEN_SOURCE_UNSUPPORTED")
    # One literal container followed by the member itself: the member names a
    # direct entry of one declared root container, never a nested location.
    if len(steps) != 2 or steps[0] is None or steps[1] is not None:
        raise ValueError("MEMBER_BINDING_TOKEN_SHAPE_UNSUPPORTED")
    return SchemaMemberLaw(reference, registry_kind, tuple(steps))


class _MemberBindingFault:
    """A member-binding rule violation carrying the witness-pointer member index."""

    __slots__ = ("member_index",)

    def __init__(self, member_index: int) -> None:
        self.member_index = member_index


class _RegistrationContentSource:
    """Row content read along the row-declared path inside the explicit root.

    A read, decode or parse failure is deliberately not a registration failure:
    the declared content_read_failure_owner keeps that ownership with the
    candidate resolution stage.
    """

    __slots__ = ("engine",)

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def content(self, row: Mapping[str, Any]) -> Any:
        declared = row.get("path")
        if not isinstance(declared, str) or not declared:
            return REGISTRATION_CONTENT_UNREADABLE
        status, value = self.engine.path_document(declared)
        return value if status == "OK" else REGISTRATION_CONTENT_UNREADABLE


class _RegistrationEvaluation:
    __slots__ = ("registry", "registered_schemas", "content_source")

    def __init__(self, engine: Any, registry: Mapping[str, Any]) -> None:
        self.registry = registry
        rows = registry.get("objects")
        self.registered_schemas = {triple for triple in
                                   (registration_row_identity(row) for row in rows
                                    if isinstance(row, Mapping) and row.get("kind") == "SCHEMA")
                                   if triple is not None} if isinstance(rows, list) else set()
        self.content_source = _RegistrationContentSource(engine)


class _RegistrationRule:
    __slots__ = ("rule_id", "diagnostic", "pointer_template", "scope", "relation", "comparator")

    def __init__(self, rule_id: str, diagnostic: str, pointer_template: str, scope: str,
                 relation: Any, comparator: Any) -> None:
        self.rule_id = rule_id
        self.diagnostic = diagnostic
        self.pointer_template = pointer_template
        self.scope = scope
        self.relation = relation
        self.comparator = comparator

    def instance_pointer(self, row_index: int, fault: Any = None) -> str:
        pointer = self.pointer_template.replace("<row_index>", str(row_index))
        if isinstance(fault, _MemberBindingFault):
            pointer = pointer.replace("<member_index>", str(fault.member_index))
        if "<" in pointer or ">" in pointer:
            raise registration_unsupported()
        return pointer

    def applies_to(self, row: Mapping[str, Any]) -> bool:
        if self.scope == "SCHEMA_ROWS_ONLY":
            return row.get("kind") == "SCHEMA"
        if self.scope == "NON_SCHEMA_ROWS_ONLY":
            return row.get("kind") != "SCHEMA"
        return True


class _RegistrationContract:
    __slots__ = ("failure_kind", "registry_identity_members", "row_version_member",
                 "schema_document_id_member", "schema_document_version_member",
                 "schema_content_id_tokens", "rules", "global_stage", "global_failure_code",
                 "global_failure_kind", "global_diagnostic", "global_key_members",
                 "global_pointer_template", "member_law")

    def __init__(self) -> None:
        self.member_law: SchemaMemberLaw | None = None
        self.failure_kind = ""
        self.registry_identity_members: tuple[str, ...] = ()
        self.row_version_member = ""
        self.schema_document_id_member = ""
        self.schema_document_version_member = ""
        self.schema_content_id_tokens: tuple[str, ...] = ()
        self.rules: list[_RegistrationRule] = []
        self.global_stage = ""
        self.global_failure_code = ""
        self.global_failure_kind = ""
        self.global_diagnostic = ""
        self.global_key_members: tuple[str, ...] = ()
        self.global_pointer_template = ""


def registration_rule_comparators(contract: _RegistrationContract) -> dict[str, Any]:
    """One comparison closure per implemented declared rule id."""
    members = tuple(contract.registry_identity_members)
    reference_member = "reference"

    def schema_kind_must_not_declare_row_schema_ref(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> bool:
        return row.get("kind") == "SCHEMA" and "schema_ref" in row

    def status_in_registry_status_vocabulary(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> bool:
        vocabulary = evaluation.registry.get("status_vocabulary")
        return not isinstance(vocabulary, list) or row.get("status") not in vocabulary

    def classification_in_registry_classification_vocabulary(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> bool:
        vocabulary = evaluation.registry.get("classification_vocabulary")
        return not isinstance(vocabulary, list) or row.get("classification") not in vocabulary

    def registration_schema_ref_resolves_to_registered_schema_row(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> bool:
        if "schema_ref" not in row:
            return False
        declared = row.get("schema_ref")
        return registration_row_identity(declared if isinstance(declared, Mapping) else {}) not in evaluation.registered_schemas

    def row_reference_equals_row_registry_identity(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> bool:
        reference = row.get(reference_member)
        return (isinstance(reference, Mapping)
                and tuple(row.get(member) for member in members) != tuple(reference.get(member) for member in members))

    def non_schema_row_content_declared_identity_equals_row_registry_identity(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> bool:
        # The identity declared by the registered content is its object_id and object_version; content that cannot
        # be read, decoded or is not an object stays with RESOLVE_CANDIDATE_OBJECTS (content_read_failure_owner).
        # The comparison is the prior candidate-loading identity rule: it covers the eligible (ACTIVE NORMATIVE) rows.
        if row.get("kind") == "SCHEMA" or row.get("status") != "ACTIVE" or row.get("classification") != "NORMATIVE":
            return False
        document = evaluation.content_source.content(row)
        if document is REGISTRATION_CONTENT_UNREADABLE or not isinstance(document, Mapping):
            return False
        return not (document.get("object_id") == row.get("id") and document.get("object_version") == row.get("version"))

    def schema_document_version_equals_row_version(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> bool:
        return row.get(contract.schema_document_version_member) != row.get(contract.row_version_member)

    def schema_document_content_id_equals_schema_document_id(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> bool:
        document = evaluation.content_source.content(row)
        if document is REGISTRATION_CONTENT_UNREADABLE:
            return False
        found = registration_pointer_value(document, contract.schema_content_id_tokens)
        expected = row.get(contract.schema_document_id_member)
        return not (isinstance(found, str) and isinstance(expected, str) and found == expected)

    def schema_row_registered_members_bind_to_root_defs_entries(evaluation: _RegistrationEvaluation, row: Mapping[str, Any]) -> Any:
        # Same row-declared content as the schema-document identity rule; an
        # unreadable document stays with the later owner and an absent members
        # array registers nothing. The first registered member whose declared
        # binding pointer does not resolve is the single reported location.
        law = contract.member_law
        if law is None:
            return False
        registered = row.get("members")
        if not isinstance(registered, list) or not registered:
            return False
        document = evaluation.content_source.content(row)
        if document is REGISTRATION_CONTENT_UNREADABLE:
            return False
        for position, member_id in enumerate(registered):
            if law.locate(document, member_id) is REGISTRATION_CONTENT_ABSENT:
                return _MemberBindingFault(position)
        return False

    return {
        "SCHEMA_KIND_MUST_NOT_DECLARE_ROW_SCHEMA_REF": schema_kind_must_not_declare_row_schema_ref,
        "STATUS_IN_REGISTRY_STATUS_VOCABULARY": status_in_registry_status_vocabulary,
        "CLASSIFICATION_IN_REGISTRY_CLASSIFICATION_VOCABULARY": classification_in_registry_classification_vocabulary,
        "REGISTRATION_SCHEMA_REF_RESOLVES_TO_REGISTERED_SCHEMA_ROW": registration_schema_ref_resolves_to_registered_schema_row,
        "ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY": row_reference_equals_row_registry_identity,
        "NON_SCHEMA_ROW_CONTENT_DECLARED_IDENTITY_EQUALS_ROW_REGISTRY_IDENTITY": non_schema_row_content_declared_identity_equals_row_registry_identity,
        "SCHEMA_DOCUMENT_VERSION_EQUALS_ROW_VERSION": schema_document_version_equals_row_version,
        "SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID": schema_document_content_id_equals_schema_document_id,
        MEMBER_BINDING_RULE_ID: schema_row_registered_members_bind_to_root_defs_entries,
    }

def declared_selection_examples(uniqueness: Mapping[str, Any]) -> None:
    """Declared selection examples must reproduce under the declared scan order.

    The examples are normative illustrations of the declared selection; if the
    evaluator's scan would select different indices, the declaration is not the
    one this evaluator implements and the evaluation fails closed.
    """
    examples = uniqueness.get("selection_examples")
    if not isinstance(examples, list) or not examples:
        raise registration_unsupported()
    for example in examples:
        occurrences = example.get("occurrence_indices_by_key") if isinstance(example, Mapping) else None
        first = example.get("selected_first_occurrence_index") if isinstance(example, Mapping) else None
        second = example.get("selected_second_occurrence_index") if isinstance(example, Mapping) else None
        if (not isinstance(occurrences, Mapping) or not occurrences
                or not isinstance(first, int) or isinstance(first, bool)
                or not isinstance(second, int) or isinstance(second, bool)):
            raise registration_unsupported()
        pairs: list[tuple[int, Any]] = []
        for key, indices in occurrences.items():
            if not isinstance(indices, list) or not indices:
                raise registration_unsupported()
            for index in indices:
                if not isinstance(index, int) or isinstance(index, bool):
                    raise registration_unsupported()
                pairs.append((index, key))
        pairs.sort(key=lambda pair: pair[0])
        if len({index for index, _ in pairs}) != len(pairs):
            raise registration_unsupported()
        chosen: tuple[int, int] | None = None
        for later in range(len(pairs)):
            for earlier in range(later):
                if pairs[earlier][1] == pairs[later][1]:
                    chosen = (pairs[earlier][0], pairs[later][0])
                    break
            if chosen is not None:
                break
        if chosen != (first, second):
            raise registration_unsupported()


def global_uniqueness_declaration(declarations: Mapping[str, Any], ownership: Mapping[str, Any],
                                  witness_contract: Mapping[str, Any],
                                  contract: _RegistrationContract) -> None:
    """Consume metacontract:/registration/global_uniqueness or fail closed.

    Identity key members, failure code, failure kind, diagnostic token and
    instance pointer template are read from the declaration; the run time stage
    uses only these declared values, never a private token or pointer.
    """
    uniqueness = declarations.get("global_uniqueness")
    roles = declarations.get("stage_roles")
    order = declarations.get("stage_order")
    tokens = declarations.get("diagnostic_tokens")
    if not isinstance(uniqueness, Mapping) or not isinstance(roles, Mapping) or not isinstance(order, list):
        raise registration_unsupported()
    if not order or not all(isinstance(stage, str) and stage for stage in order):
        raise registration_unsupported()
    stage = uniqueness.get("stage")
    if uniqueness.get("stage_role") != GLOBAL_UNIQUENESS_ROLE or roles.get(GLOBAL_UNIQUENESS_ROLE) != stage:
        raise registration_unsupported()
    if stage != GLOBAL_UNIQUENESS_STAGE or order.count(stage) != 1:
        raise registration_unsupported()
    position = order.index(stage)
    if position < 2:
        raise registration_unsupported()
    if order[position - 2:position] != uniqueness.get("preceding_stages") or order[position + 1] != uniqueness.get("following_stage"):
        raise registration_unsupported()
    members = uniqueness.get("identity_key_members")
    if not isinstance(members, list) or len(members) != 3 or not all(isinstance(member, str) and member for member in members):
        raise registration_unsupported()
    if uniqueness.get("identity_key_source") != "REGISTRY_DECLARED_IDENTITY_FIELDS_AND_UNIQUENESS_KEY":
        raise registration_unsupported()
    if uniqueness.get("identity_key_declaration") != "SAME_KEY_NO_ADDITIONAL_KEY_DEFINED":
        raise registration_unsupported()
    if uniqueness.get("row_scope") != "ALL_REGISTRY_ROWS_REGARDLESS_OF_STATUS_AND_CLASSIFICATION":
        raise registration_unsupported()
    failure_code = uniqueness.get("failure_code")
    failure_kind = uniqueness.get("failure_kind")
    diagnostic = uniqueness.get("diagnostic")
    bucket = uniqueness.get("diagnostic_token_bucket")
    if failure_code != REGISTRATION_FAILURE_CODE or witness_contract.get("code") != failure_code:
        raise registration_unsupported()
    if not isinstance(failure_kind, str) or not failure_kind:
        raise registration_unsupported()
    if not isinstance(diagnostic, str) or not diagnostic:
        raise registration_unsupported()
    if not isinstance(tokens, Mapping) or not isinstance(bucket, str) or tokens.get(bucket) != [diagnostic]:
        raise registration_unsupported()
    if uniqueness.get("witness_ref") != "registration.witness_contract" or uniqueness.get("witness_fields") != "THE_SEVEN_FIELDS_OF_REGISTRATION_WITNESS_CONTRACT":
        raise registration_unsupported()
    if uniqueness.get("additional_witness_fields") != "FORBIDDEN":
        raise registration_unsupported()
    if uniqueness.get("result_contract_ref") != GLOBAL_UNIQUENESS_RESULT_CONTRACT_REF:
        raise registration_unsupported()
    if uniqueness.get("instance_pointer") != GLOBAL_UNIQUENESS_POINTER_TEMPLATE:
        raise registration_unsupported()
    if uniqueness.get("bound_identity") != "SELECTED_DUPLICATED_KIND_ID_VERSION_TRIPLE_OBJECT" or uniqueness.get("first_failure_only") is not True:
        raise registration_unsupported()
    selection = uniqueness.get("selection")
    if not isinstance(selection, Mapping):
        raise registration_unsupported()
    for name, token in GLOBAL_UNIQUENESS_SELECTION_TOKENS.items():
        if selection.get(name) != token:
            raise registration_unsupported()
    precedence = uniqueness.get("precedence")
    if not isinstance(precedence, Mapping):
        raise registration_unsupported()
    for name in ("earlier_structural_or_semantic_failure_wins", "duplicate_wins_over_every_later_integrity_failure",
                 "first_failure_only", "stop_after_first_failure"):
        if precedence.get(name) is not True:
            raise registration_unsupported()
    unreached = precedence.get("unreached_after_duplicate")
    if not isinstance(unreached, list) or not unreached:
        raise registration_unsupported()
    for stage_token in unreached:
        if not isinstance(stage_token, str) or not stage_token:
            raise registration_unsupported()
    if unreached[0] != uniqueness.get("following_stage"):
        raise registration_unsupported()
    if [stage_token for stage_token in order[position + 1:] if stage_token in set(unreached)] != unreached:
        raise registration_unsupported()
    if uniqueness.get("duplicate_identity_repair") != "FORBIDDEN" or uniqueness.get("cross_source_collision_repair") != "FORBIDDEN":
        raise registration_unsupported()
    declared_selection_examples(uniqueness)
    owned = ownership.get("global_uniqueness_owned")
    if not isinstance(owned, list) or len(owned) != 1 or not isinstance(owned[0], Mapping):
        raise registration_unsupported()
    declared = owned[0]
    if declared.get("property") != GLOBAL_UNIQUENESS_PROPERTY or declared.get("stage") != stage:
        raise registration_unsupported()
    if declared.get("failure_code") != failure_code or declared.get("failure_kind") != failure_kind:
        raise registration_unsupported()
    if declared.get("diagnostic") != diagnostic or declared.get("diagnostic_token_bucket") != bucket:
        raise registration_unsupported()
    if declared.get("identity_key_members") != members or declared.get("row_scope") != uniqueness.get("row_scope"):
        raise registration_unsupported()
    if declared.get("identity_key_source") != uniqueness.get("identity_key_source") or declared.get("witness_ref") != uniqueness.get("witness_ref"):
        raise registration_unsupported()
    if declared.get("first_failure_only") is not True:
        raise registration_unsupported()
    if declared.get("selection") != "ASCENDING_MINIMAL_SECOND_OCCURRENCE_J_THEN_MINIMAL_PRIOR_I":
        raise registration_unsupported()
    mirrors = ownership.get("ast_uniqueness_defensive_mirrors")
    if not isinstance(mirrors, list) or len(mirrors) != 2:
        raise registration_unsupported()
    mirror_assertions: set[tuple[Any, Any]] = set()
    for mirror in mirrors:
        if not isinstance(mirror, Mapping):
            raise registration_unsupported()
        if mirror.get("owner") != GLOBAL_UNIQUENESS_ROLE or mirror.get("role") != "DEFENSIVE_MIRROR":
            raise registration_unsupported()
        if mirror.get("reachability") != "UNREACHABLE_AFTER_GLOBAL_UNIQUENESS_PASSES":
            raise registration_unsupported()
        if mirror.get("mirrors_stage") != stage or mirror.get("mirrors_property") != GLOBAL_UNIQUENESS_PROPERTY:
            raise registration_unsupported()
        if not isinstance(mirror.get("assertion_id"), str) or not mirror.get("assertion_id"):
            raise registration_unsupported()
        mirror_assertions.add((mirror.get("procedure_id"), mirror.get("assertion_id")))
    distinct = ownership.get("ast_uniqueness_distinct_owned")
    if not isinstance(distinct, list) or len(distinct) != 2:
        raise registration_unsupported()
    for entry in distinct:
        if not isinstance(entry, Mapping) or entry.get("owner") != "AST" or entry.get("role") != "DISTINCT_LATER_PROPERTY":
            raise registration_unsupported()
        if entry.get("mirrors_semantic_registration") is not False or entry.get("mirrors_global_uniqueness") is not False:
            raise registration_unsupported()
        if (entry.get("procedure_id"), entry.get("assertion_id")) in mirror_assertions:
            raise registration_unsupported()
    contract.global_stage = stage
    contract.global_failure_code = failure_code
    contract.global_failure_kind = failure_kind
    contract.global_diagnostic = diagnostic
    contract.global_key_members = tuple(members)
    contract.global_pointer_template = GLOBAL_UNIQUENESS_POINTER_TEMPLATE


def registration_contract(declarations: Mapping[str, Any], metacontract: Mapping[str, Any] | None = None) -> _RegistrationContract:
    """Validate the machine-readable registration declarations and derive the plan."""
    roles = declarations.get("stage_roles")
    semantic = declarations.get("semantic_validation")
    identity_declaration = semantic.get("schema_document_identity") if isinstance(semantic, Mapping) else None
    ownership = declarations.get("constraint_ownership")
    witness_contract = declarations.get("witness_contract")
    ordering = declarations.get("first_failure_ordering")
    if (not isinstance(roles, Mapping) or not isinstance(semantic, Mapping) or not isinstance(identity_declaration, Mapping)
            or not isinstance(ownership, Mapping) or not isinstance(witness_contract, Mapping) or not isinstance(ordering, Mapping)):
        raise registration_unsupported()
    if roles.get(REGISTRATION_SEMANTIC_ROLE) != REGISTRATION_SEMANTIC_STAGE or semantic.get("stage") != REGISTRATION_SEMANTIC_STAGE:
        raise registration_unsupported()
    if (semantic.get("instance_scope") != REGISTRATION_INSTANCE_SCOPE or semantic.get("failure_code") != REGISTRATION_FAILURE_CODE
            or semantic.get("witness_object_role") != REGISTRATION_OBJECT_ROLE or semantic.get("first_failure_only") is not True):
        raise registration_unsupported()
    failure_kind = semantic.get("failure_kind")
    if not isinstance(failure_kind, str) or not failure_kind:
        raise registration_unsupported()
    if (witness_contract.get("status") != "FAIL" or witness_contract.get("stage") != REGISTRATION_FAILURE_STAGE
            or witness_contract.get("code") != REGISTRATION_FAILURE_CODE or witness_contract.get("argument") != "object_registry"
            or witness_contract.get("object_role") != REGISTRATION_OBJECT_ROLE or witness_contract.get("schema_ref") != REGISTRATION_SCHEMA_ID
            or witness_contract.get("additional_witness_fields") != "FORBIDDEN"
            or witness_contract.get("bound_identity") != REGISTRATION_BOUND_IDENTITY_TOKEN):
        raise registration_unsupported()
    declared_witness_fields = witness_contract.get("witness_fields")
    if not isinstance(declared_witness_fields, list) or tuple(declared_witness_fields) != REGISTRATION_WITNESS_FIELDS:
        raise registration_unsupported()
    if (ordering.get("within_stage") != "ASCENDING_ROW_INDEX_THEN_DECLARED_RULE_ORDER_THEN_SINGLE_POINTER"
            or ordering.get("row_index") != "ZERO_BASED_ARRAY_INDEX_OF_/objects"
            or ordering.get("first_failure_only") is not True or ordering.get("stop_after_first_failure") is not True):
        raise registration_unsupported()
    registry_members = identity_declaration.get("registry_identity_members")
    document_members = identity_declaration.get("schema_document_identity_members")
    content_tokens = registration_pointer_tokens(identity_declaration.get("schema_content_id_member"))
    if (not isinstance(registry_members, list) or not registry_members
            or not all(isinstance(member, str) and member for member in registry_members)):
        raise registration_unsupported()
    if (not isinstance(document_members, list) or len(document_members) != 2
            or not all(isinstance(member, str) and member for member in document_members)):
        raise registration_unsupported()
    if not content_tokens or any(not isinstance(token, str) or not token for token in content_tokens):
        raise registration_unsupported()
    row_version_member = registry_members[-1]
    if (identity_declaration.get("registry_id_to_schema_document_id_convention") != "NONE"
            or identity_declaration.get("schema_document_id_source") != "STORED_ROW_MEMBER_ONLY_NO_EVALUATOR_SIDE_DERIVATION"
            or identity_declaration.get("schema_content_id_equality") != "EXACT_JSON_STRING_EQUALITY"
            or identity_declaration.get("schema_document_version_equality") != "EXACT_JSON_STRING_EQUALITY_TO_ROW_" + row_version_member.upper()
            or identity_declaration.get("schema_artifact_version_member") != "ABSENT_NEVER_CONSULTED"
            or identity_declaration.get("content_read_failure_owner") != "RESOLVE_CANDIDATE_OBJECTS_UNCHANGED"
            or identity_declaration.get("reference_equals_registry_identity") is not True):
        raise registration_unsupported()
    declared_rules = semantic.get("rules")
    if not isinstance(declared_rules, list) or not declared_rules:
        raise registration_unsupported()
    contract = _RegistrationContract()
    contract.failure_kind = failure_kind
    contract.registry_identity_members = tuple(registry_members)
    contract.row_version_member = row_version_member
    contract.schema_document_id_member = document_members[0]
    contract.schema_document_version_member = document_members[1]
    contract.schema_content_id_tokens = tuple(content_tokens)
    comparators = registration_rule_comparators(contract)
    for declared_rule in declared_rules:
        if not isinstance(declared_rule, Mapping):
            raise registration_unsupported()
        rule_id = declared_rule.get("rule_id")
        diagnostic = declared_rule.get("diagnostic")
        pointer_template = declared_rule.get("instance_pointer")
        condition = declared_rule.get("condition")
        relation = declared_rule.get("relation_to_prior_rule")
        if (not isinstance(rule_id, str) or not isinstance(diagnostic, str) or not isinstance(pointer_template, str)
                or not pointer_template.startswith(REGISTRATION_POINTER_PREFIX) or not isinstance(condition, str)):
            raise registration_unsupported()
        scope = declared_rule.get("row_scope")
        if scope is None:
            scope = "ALL_ROWS"
        if scope not in REGISTRATION_ROW_SCOPES:
            raise registration_unsupported()
        required_scopes = REGISTRATION_RULE_SCOPES.get(rule_id)
        if required_scopes is not None and scope not in required_scopes:
            raise registration_unsupported()
        if rule_id == "NON_SCHEMA_ROW_CONTENT_DECLARED_IDENTITY_EQUALS_ROW_REGISTRY_IDENTITY":
            if relation not in REGISTRATION_UNCHANGED_RELATIONS:
                raise registration_unsupported()
        elif relation is not None and relation not in REGISTRATION_UNCHANGED_RELATIONS:
            raise registration_unsupported()
        markers = REGISTRATION_CONDITION_MARKERS.get(rule_id)
        comparator = comparators.get(rule_id)
        if comparator is None or markers is None or any(marker not in condition for marker in markers):
            raise registration_unsupported()
        placeholders = set(re.findall(r"<[^<>]+>", pointer_template)) - {"<row_index>"}
        if rule_id == MEMBER_BINDING_RULE_ID:
            if placeholders - {"<member_index>"} or contract.member_law is not None or metacontract is None:
                raise registration_unsupported()
            if (declared_rule.get("member_selection") != "LOWEST_MEMBER_INDEX_WHOSE_BINDING_POINTER_DOES_NOT_RESOLVE"
                    or declared_rule.get("absent_members") != "NO_REGISTERED_MEMBERS_NO_FAILURE"
                    or declared_rule.get("content_source") != "SAME_ROW_DECLARED_CONTENT_BYTES_AND_STRICT_UTF8_JSON_PARSE_AS_SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID"
                    or declared_rule.get("content_read_failure_owner") != "RESOLVE_CANDIDATE_OBJECTS_UNCHANGED"):
                raise registration_unsupported()
            try:
                law = declared_member_law(metacontract, declared_rule.get("binding_ref"))
            except ValueError:
                law = None
            contract.member_law = law if law is not None and law.registry_kind == "SCHEMA" else None
        elif placeholders:
            raise registration_unsupported()
        contract.rules.append(_RegistrationRule(rule_id, diagnostic, pointer_template, scope, relation, comparator))
    positions = {rule.rule_id: (position, rule.diagnostic) for position, rule in enumerate(contract.rules)}
    if len(positions) != len(contract.rules):
        raise registration_unsupported()
    declared_ids = ownership.get("schema_identity_ordered_rule_ids")
    declared_diagnostics = ownership.get("schema_identity_ordered_diagnostics")
    if (not isinstance(declared_ids, list) or not isinstance(declared_diagnostics, list) or not declared_ids
            or len(declared_ids) != len(declared_diagnostics)):
        raise registration_unsupported()
    ordered_positions: list[int] = []
    for rule_id, diagnostic in zip(declared_ids, declared_diagnostics):
        entry = positions.get(rule_id)
        if entry is None or entry[1] != diagnostic:
            raise registration_unsupported()
        ordered_positions.append(entry[0])
    if ordered_positions != sorted(ordered_positions) or len(set(ordered_positions)) != len(ordered_positions):
        raise registration_unsupported()
    if ownership.get("schema_identity_defect_first_failure_stage") != REGISTRATION_SEMANTIC_STAGE:
        raise registration_unsupported()
    if ownership.get("ast_schema_identity_assertions_are_never_first_failure") is not True:
        raise registration_unsupported()
    unchanged = ownership.get("non_schema_content_identity")
    if not isinstance(unchanged, Mapping) or unchanged.get("semantics") != "UNCHANGED":
        raise registration_unsupported()
    owned = ownership.get("semantic_registration_owned")
    if not isinstance(owned, list) or not owned:
        raise registration_unsupported()
    for entry in owned:
        entry_ids = entry.get("rule_ids") if isinstance(entry, Mapping) else None
        if (not isinstance(entry_ids, list) or not entry_ids or any(rule_id not in positions for rule_id in entry_ids)
                or entry.get("stage") != REGISTRATION_SEMANTIC_STAGE or entry.get("failure_code") != REGISTRATION_FAILURE_CODE
                or entry.get("failure_kind") != failure_kind):
            raise registration_unsupported()
    mirrors = ownership.get("ast_defensive_mirrors")
    if not isinstance(mirrors, list):
        raise registration_unsupported()
    for mirror in mirrors:
        if (not isinstance(mirror, Mapping) or mirror.get("mirrors_rule_id") not in positions
                or mirror.get("role") != "DEFENSIVE_MIRROR"
                or mirror.get("reachability") != "UNREACHABLE_AFTER_SEMANTIC_REGISTRATION_PASSES"):
            raise registration_unsupported()
    distinct = ownership.get("ast_distinct_owned")
    if not isinstance(distinct, list):
        raise registration_unsupported()
    for entry in distinct:
        if (not isinstance(entry, Mapping) or entry.get("owner") != "AST"
                or entry.get("mirrors_semantic_registration") is not False):
            raise registration_unsupported()
    if declarations.get("later_identical_checks") != "DEFENSIVE_UNREACHABLE":
        raise registration_unsupported()
    tokens = declarations.get("diagnostic_tokens")
    declared_tokens = tokens.get(failure_kind) if isinstance(tokens, Mapping) else None
    if declared_tokens != list(dict.fromkeys(rule.diagnostic for rule in contract.rules)):
        raise registration_unsupported()
    global_uniqueness_declaration(declarations, ownership, witness_contract, contract)
    return contract



# ---------------------------------------------------------------------------
# Pre-execution failure framework: every failure is emitted from a declared model family/condition.
# ---------------------------------------------------------------------------
class Subj:
    """The subject a condition was evaluated on (its class is one of closed_vocabularies.subject_class)."""

    def __init__(self, cls: str, **attrs: Any):
        self.cls = cls
        self.__dict__.update(attrs)


class Hit:
    """A condition hit; `case` selects by_case witness rules, the rest are facts gathered by the predicate."""

    def __init__(self, case: str | None = None, **facts: Any):
        self.case = case
        self.__dict__.update(facts)


class PreExecFailure(Exception):
    def __init__(self, result: dict[str, Any]):
        super().__init__("PRE_EXECUTION_FAILURE")
        self.result = result


class X:
    """Emission context: the engine, family, condition, subject and hit of one failure."""

    def __init__(self, eng: "Engine", fam: dict[str, Any], cond: dict[str, Any], subj: Subj, hit: Hit):
        self.eng, self.fam, self.cond, self.subj, self.hit = eng, fam, cond, subj, hit

    def owning(self) -> str:
        owner = self.cond.get("owning_object", self.fam.get("owning_object"))
        if isinstance(self.fam.get("owning_object"), dict):
            owner = self.fam["owning_object"]["by_binding_site"][self.subj.site]
        if owner not in BOOTSTRAP_OBJECTS:
            raise ModelGap("OWNING_OBJECT_UNDECLARED")
        return owner


DERIVE: dict[tuple[str, str], Any] = {}


def derivation(field: str, *tokens: str):
    def register(function):
        for token in tokens:
            DERIVE[(field, token)] = function
        return function
    return register


def derive(x: X, field: str, token: str) -> Any:
    definition = DV[field][token]
    if "constant_value" in definition:
        return copy.deepcopy(definition["constant_value"])
    function = DERIVE.get((field, token))
    if function is None:
        raise ModelGap("DERIVATION_NOT_IMPLEMENTED:" + field + "." + token)
    return function(x)


_CONTRACT_VOCABULARY = {"TRUST_RESULT": "trust_result", "MAP_VALUE_COMPARISON": "map_value_comparison"}


def vocabulary_group(contract_name: str, field: str) -> str:
    """The derivation_vocabulary group that defines the tokens of a witness field of the given contract."""
    return _CONTRACT_VOCABULARY.get(contract_name, field)


def resolve_rule(x: X, field: str, rule: Mapping[str, Any]) -> Any:
    if "derivation" in rule:
        return derive(x, vocabulary_group(x.fam["witness_contract"], field), rule["derivation"])
    if "constant" in rule:
        return copy.deepcopy(rule["constant"])
    if "by_subject_class" in rule:
        return resolve_rule(x, field, rule["by_subject_class"][x.subj.cls])
    if "by_case" in rule:
        return resolve_rule(x, field, rule["by_case"][x.hit.case])
    raise ModelGap("WITNESS_FIELD_RULE_UNSUPPORTED:" + field)


def resolve_reason(x: X, reason: Any) -> Any:
    if isinstance(reason, str):
        return reason
    if "by_case" in reason:
        return reason["by_case"][x.hit.case]
    if "by_claim_index" in reason:
        return reason["by_claim_index"].get(str(x.subj.index), reason["otherwise"])
    raise ModelGap("REASON_RULE_UNSUPPORTED")


def family_code(x: X) -> str:
    fam = x.fam
    if "code" in fam:
        return fam["code"]
    derived = fam["code_derivation"]
    if x.fam["family_id"] == "PE-11":
        return derived[x.cond["condition_id"]]
    if x.fam["family_id"] == "PE-17":
        return derived["SOURCE_VECTOR_CATALOG"] if x.subj.ref_kind == "SOURCE_VECTOR_CATALOG" else derived["OTHERWISE"]
    if x.fam["family_id"] == "PE-18":
        return x.subj.claim["failure_code"]
    raise ModelGap("CODE_DERIVATION_UNSUPPORTED")


def build_failure(eng: "Engine", family_id: str, condition_id: str, subj: Subj, hit: Hit) -> PreExecFailure:
    fam = FAMILIES[family_id]
    cond = next(row for row in fam["conditions"] if row["condition_id"] == condition_id)
    x = X(eng, fam, cond, subj, hit)
    contract_name = fam["witness_contract"]
    contract = MODEL["witness_contracts"][contract_name]
    if contract_name == "TRUST_RESULT":
        witness = {name: resolve_rule(x, name, rule) for name, rule in cond["witness"].items()}
        trust = {"status": "FAIL", "code": family_code(x), "witness": witness}
        return PreExecFailure({"status": "FAIL", "stage": "TRUST", "trust_result": trust,
                               "counts": {"procedures": 0, "invariants": 0, "rules": 0}})
    code = family_code(x)
    if contract_name in ("SEVEN_FIELD", "STATIC_VALIDATION"):
        witness = {}
        for name in contract["fields"]:
            if name == "failure_kind":
                witness[name] = contract.get("failure_kind", cond.get("failure_kind"))
            elif name == "diagnostic":
                witness[name] = cond["diagnostic"]
            else:
                witness[name] = resolve_rule(x, name, cond["witness"][name])
    elif contract_name == "PROFILE_PREFLIGHT":
        witness = {}
        for name in contract["fields"]:
            if name == "operation":
                witness[name] = REGISTERED_PREFLIGHT_OPERATIONS[code]
            elif name == "reason":
                witness[name] = resolve_reason(x, cond["reason"])
            elif name == "diagnostic":
                witness[name] = cond["diagnostic"]
            else:
                witness[name] = resolve_rule(x, name, cond["witness"][name])
    elif contract_name == "MAP_VALUE_COMPARISON":
        witness = {name: resolve_rule(x, name, rule) for name, rule in cond["witness"].items()}
        witness["reason"] = resolve_reason(x, cond["reason"])
    elif contract_name == "STRICT_UNION_COLLISION":
        witness = strict_union_witness(x)
    elif contract_name == "VECTOR_REGISTRY_CLAIM":
        witness = vector_claim_witness(x)
    else:
        raise ModelGap("WITNESS_CONTRACT_UNSUPPORTED:" + contract_name)
    return PreExecFailure({"status": "FAIL", "stage": "PRE_EXECUTION", "code": code, "witness": witness})


# ---------------------------------------------------------------------------
# Derivations: one implementation per derivation_vocabulary token, each from its declared definition.
# ---------------------------------------------------------------------------
def _sub(template: str, **values: Any) -> str:
    for name, value in values.items():
        template = template.replace("<" + name + ">", str(value))
    return template


# --- argument -------------------------------------------------------------
@derivation("argument", "ENTRYPOINT_ARGUMENT")
def _d_entrypoint_argument(x: X) -> Any:
    return x.subj.entry["argument"]


@derivation("argument", "OWNING_BOOTSTRAP_OBJECT_ARGUMENT")
def _d_owning_argument(x: X) -> Any:
    return BOOTSTRAP_OBJECTS[x.owning()]["argument"]


@derivation("argument", "RESERVED_INPUT_NAME")
def _d_reserved_name(x: X) -> Any:
    return x.subj.row["name"]


@derivation("argument", "REGISTRATION_WITNESS_ARGUMENT")
def _d_registration_argument(x: X) -> Any:
    return REGISTRATION["witness_contract"]["argument"]


# --- object_role ----------------------------------------------------------
@derivation("object_role", "REGISTERED_KIND_OF_FAILING_OBJECT")
def _d_failing_kind(x: X) -> Any:
    return x.subj.row["kind"]


@derivation("object_role", "ENTRYPOINT_KIND")
def _d_entrypoint_kind(x: X) -> Any:
    return x.subj.entry["registered_kind"]


@derivation("object_role", "REGISTERED_KIND_OF_OWNING_OBJECT")
def _d_owning_registered_kind(x: X) -> Any:
    return BOOTSTRAP_OBJECTS[x.owning()]["registered_kind"]


@derivation("object_role", "RESERVED_INPUT_DECLARED_TYPE")
def _d_reserved_type(x: X) -> Any:
    return x.subj.row["type"]


@derivation("object_role", "REGISTRATION_WITNESS_OBJECT_ROLE")
def _d_registration_role(x: X) -> Any:
    return REGISTRATION["witness_contract"]["object_role"]


@derivation("object_role", "OWNING_OBJECT_REGISTRY_ROW_KIND")
def _d_owning_row_kind(x: X) -> Any:
    return x.eng.owning_identity(x.owning())["kind"]


@derivation("object_role", "ALLOWLIST_REF_KIND")
def _d_allowlist_kind(x: X) -> Any:
    return x.subj.row["ref"]["kind"]


# --- schema_ref -----------------------------------------------------------
@derivation("schema_ref", "APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID")
def _d_applied_schema_id(x: X) -> Any:
    return x.eng.schema_document_id(x.subj.row.get("schema_ref"))


@derivation("schema_ref", "ENTRYPOINT_SCHEMA_DOCUMENT_ID")
def _d_entrypoint_schema_id(x: X) -> Any:
    return x.subj.entry["schema_document_id"]


@derivation("schema_ref", "OWNING_OBJECT_SCHEMA_DOCUMENT_ID")
def _d_owning_schema_id(x: X) -> Any:
    return BOOTSTRAP_OBJECTS[x.owning()]["schema_document_id"]


@derivation("schema_ref", "PRODUCER_SCHEMA_ROW_SCHEMA_DOCUMENT_ID")
def _d_producer_schema_id(x: X) -> Any:
    return x.eng.schema_document_id(x.subj.row["profile_content_source"]["producer_schema_ref"])


@derivation("schema_ref", "DRAFT_2020_12_METASCHEMA")
def _d_metaschema(x: X) -> Any:
    return DRAFT_2020_12


@derivation("schema_ref", "RUNTIME_VALUE_SCHEMA_ID")
def _d_runtime_schema_id(x: X) -> Any:
    name = "verification_universe" if x.subj.cls == "UNIVERSE_VALUE" else "resolved_object"
    return x.eng.metacontract["runtime_representation"]["value_schemas"][name]["$id"]


@derivation("schema_ref", "REGISTRATION_WITNESS_SCHEMA_REF")
def _d_registration_schema_ref(x: X) -> Any:
    return REGISTRATION["witness_contract"]["schema_ref"]


@derivation("schema_ref", "STRUCTURAL_APPLICATION_SCHEMA_DOCUMENT_ID")
def _d_structural_schema_id(x: X) -> Any:
    return REGISTRATION["structural_application"]["schema_id"]


@derivation("schema_ref", "OWNING_OBJECT_APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID")
def _d_owning_applied_schema_id(x: X) -> Any:
    return x.eng.owning_applied_schema_id(x.owning())


@derivation("schema_ref", "ALLOWLIST_EXPECTED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID")
def _d_allowlist_schema_id(x: X) -> Any:
    return x.eng.schema_document_id(x.subj.row["expected_schema_ref"])


# --- instance_pointer -----------------------------------------------------
@derivation("instance_pointer", "FIRST_INVALID_LOCATION_CANONICAL_PREORDER", "FIRST_UNCANONICALIZABLE_NUMBER_CANONICAL_PREORDER",
            "FIRST_NONLOCAL_REFERENCE_CANONICAL_PREORDER", "STATIC_VIOLATION_LOCATION", "WITNESS_OPERAND_TERMINAL",
            "BINDING_DECLARATION_LOCATION", "REGISTRY_LEVEL_FIRST_INVALID_LOCATION")
def _d_hit_pointer(x: X) -> Any:
    return x.hit.pointer


@derivation("instance_pointer", "SCOPED_FIRST_INVALID_LOCATION")
def _d_scoped_pointer(x: X) -> Any:
    scope = _sub(x.cond["pointer_scope"], row_index=x.subj.index if hasattr(x.subj, "index") else "",
                 escaped_value_schema_name=encode_pointer_token(getattr(x.subj, "name", "")),
                 k=getattr(x.subj, "k", ""))
    return scope + pointer_of(x.hit.tokens)


@derivation("instance_pointer", "PACKAGE_SELF_DIGEST_DECLARATION_LOCATION")
def _d_self_digest_location(x: X) -> Any:
    return x.hit.pointer


@derivation("instance_pointer", "RESERVED_INPUT_MEMBER_LOCATION")
def _d_reserved_member_location(x: X) -> Any:
    return x.hit.pointer


@derivation("instance_pointer", "RESERVED_INPUT_COLLECTION_LOCATION")
def _d_reserved_collection_location(x: X) -> Any:
    return x.cond["collection_pointer"]


@derivation("instance_pointer", "ROW_POINTER_TEMPLATE")
def _d_row_template(x: X) -> Any:
    second = x.subj.second if hasattr(x.subj, "second") else ""
    member_index = getattr(x.hit, "member_index", "")
    return _sub(x.cond["pointer_template"], row_index=getattr(x.subj, "index", ""), second_occurrence_index=second,
                member_index=member_index)


@derivation("instance_pointer", "DECLARED_SECTION_POINTER")
def _d_section_pointer(x: X) -> Any:
    return x.cond["section_pointer"]


@derivation("instance_pointer", "ENTRYPOINT_BINDING_LOCATION")
def _d_entrypoint_binding(x: X) -> Any:
    return x.cond["binding_pointer"]


@derivation("instance_pointer", "REGISTRY_BINDING_LOCATION")
def _d_registry_binding(x: X) -> Any:
    return _sub(x.cond["binding_pointer"], row_index=getattr(x.hit, "row_index", ""))


@derivation("instance_pointer", "BOOTSTRAP_ROW_LOCATION")
def _d_bootstrap_location(x: X) -> Any:
    cases = DV["instance_pointer"]["BOOTSTRAP_ROW_LOCATION"]["cases"]
    return _sub(cases[x.hit.case], row_index=getattr(x.hit, "row_index", ""))


@derivation("instance_pointer", "PRODUCER_SCHEMA_REF_DECLARATION_LOCATION")
def _d_producer_ref_location(x: X) -> Any:
    return "/reserved_inputs/%d/profile_content_source/producer_schema_ref" % x.subj.index


@derivation("instance_pointer", "ALLOWLIST_EXPECTED_SCHEMA_REF_DECLARATION_LOCATION")
def _d_allowlist_ref_location(x: X) -> Any:
    return "/accepted_source_allowlist/%d/expected_schema_ref" % x.subj.index


@derivation("instance_pointer", "PACKAGE_IDENTITY_MEMBER_LOCATION")
def _d_package_identity_location(x: X) -> Any:
    return "/" + x.hit.member


# --- bound_identity -------------------------------------------------------
@derivation("bound_identity", "ENTRYPOINT_CONTENT_IDENTITY_WHEN_VALID_ELSE_NULL")
def _d_entrypoint_identity(x: X) -> Any:
    return x.eng.entrypoint_content_identity(x.subj.entry)


@derivation("bound_identity", "REGISTRY_CONTENT_IDENTITY_WHEN_VALID_ELSE_NULL")
def _d_registry_content_identity(x: X) -> Any:
    return x.eng.entrypoint_content_identity(next(row for row in ENTRYPOINTS if row["registered_kind"] == "REGISTRY"))


@derivation("bound_identity", "REGISTRY_IDENTITY_OF_FAILING_OBJECT")
def _d_failing_identity(x: X) -> Any:
    return typed_identity(x.subj.row)


@derivation("bound_identity", "OWNING_OBJECT_IDENTITY")
def _d_owning_identity(x: X) -> Any:
    return copy.deepcopy(BOOTSTRAP_OBJECTS[x.owning()]["identity"])


@derivation("bound_identity", "FROZEN_SOURCE_TYPED_IDENTITY")
def _d_frozen_identity_bound(x: X) -> Any:
    return copy.deepcopy(x.subj.frozen["typed_identity"])


@derivation("bound_identity", "RESERVED_INPUT_FROZEN_SOURCE_IDENTITY_ELSE_NULL")
def _d_reserved_frozen_identity(x: X) -> Any:
    tokens = x.subj.row["profile_content_source"].get("pin_pointer_tokens")
    if not (isinstance(tokens, list) and len(tokens) == 2 and tokens[0] == "frozen_authority_pins"):
        return None
    entry = next((row for row in PC["frozen_sources"] if row["profile_member"] == tokens[1]), None)
    return copy.deepcopy(entry["typed_identity"]) if entry else None


@derivation("bound_identity", "RESOLVED_OBJECT_IDENTITY_CONTAINING_LOCATION_ELSE_NULL")
def _d_resolved_identity(x: X) -> Any:
    tokens = x.hit.tokens if x.subj.cls == "UNIVERSE_VALUE" else ["objects", x.subj.k] + list(x.hit.tokens)
    if len(tokens) < 2 or tokens[0] != "objects" or not isinstance(tokens[1], int):
        return None
    record = lookup(x.eng.universe_view, [str(t) for t in tokens[:2]])
    if record is _ABSENT or not isinstance(record, Mapping):
        return None
    return typed_identity(record.get("ref"))


@derivation("bound_identity", "REGISTRATION_WITNESS_BOUND_IDENTITY")
def _d_registration_bound(x: X) -> Any:
    return typed_identity(x.subj.row)


@derivation("bound_identity", "GLOBAL_UNIQUENESS_SELECTED_DUPLICATE_IDENTITY")
def _d_duplicate_identity(x: X) -> Any:
    return typed_identity(x.subj.row)


@derivation("bound_identity", "REGISTRY_SCHEMA_ROW_IDENTITY_WHEN_UNIQUE_READABLE_ELSE_NULL")
def _d_schema_row_identity(x: X) -> Any:
    return x.hit.identity


@derivation("bound_identity", "OWNING_OBJECT_REGISTRY_IDENTITY")
def _d_owning_registry_identity(x: X) -> Any:
    return x.eng.owning_identity(x.owning())


@derivation("bound_identity", "BOOTSTRAP_ROW_IDENTITY_ELSE_NULL")
def _d_bootstrap_identity(x: X) -> Any:
    return typed_identity(x.hit.row) if x.hit.case != "ROW_ABSENT_OR_NOT_UNIQUE" else None


@derivation("bound_identity", "ALLOWLIST_REF_IDENTITY")
def _d_allowlist_identity(x: X) -> Any:
    return typed_identity(x.subj.row["ref"])


# --- profile_pointer ------------------------------------------------------
@derivation("profile_pointer", "FIRST_INVALID_LOCATION_CANONICAL_PREORDER")
def _d_profile_first_invalid(x: X) -> Any:
    return x.hit.pointer


@derivation("profile_pointer", "FIRST_REQUIRED_PROFILE_MEMBER")
def _d_first_required_member(x: X) -> Any:
    return x.hit.entry["profile_pointer"]


@derivation("profile_pointer", "FROZEN_CONTENT_POINTER")
def _d_frozen_content_pointer(x: X) -> Any:
    return "/frozen_authority_contents/" + encode_pointer_token(x.subj.frozen["profile_member"]) + "/content_base64"


@derivation("profile_pointer", "ACCEPTED_CONTENT_ROW_POINTER")
def _d_accepted_row_pointer(x: X) -> Any:
    return "%s/%d" % (FAMILIES["PE-17"]["content_row_matching"]["collection_pointer"], x.hit.content_index)


@derivation("profile_pointer", "CLAIM_PROFILE_POINTER")
def _d_claim_profile_pointer(x: X) -> Any:
    return x.subj.claim["profile_pointer_rfc6901"]


@derivation("profile_pointer", "CONTENT_ROW_COLLECTION_POINTER")
def _d_content_collection_pointer(x: X) -> Any:
    return FAMILIES["PE-17"]["content_row_matching"]["collection_pointer"]


# --- candidate_artifact / candidate_pointer / source_identity ---------------
@derivation("candidate_artifact", "CLAIM_CANDIDATE_ARTIFACT")
def _d_claim_artifact(x: X) -> Any:
    return x.subj.claim["candidate_artifact"]


@derivation("candidate_pointer", "CLAIM_CANDIDATE_POINTER")
def _d_claim_candidate_pointer(x: X) -> Any:
    return x.subj.claim["candidate_pointer_rfc6901"]


@derivation("candidate_pointer", "SELECTOR_DECLARATION_POINTER")
def _d_selector_declaration_pointer(x: X) -> Any:
    index = next(i for i, row in enumerate(PC["claim_comparisons"]) if "candidate_selector" in row)
    return "/external_acceptance_profile_contract/candidate_claim_comparisons/%d/candidate_selector" % index


@derivation("candidate_pointer", "SELECTED_VALUE_POINTER")
def _d_selected_value_pointer(x: X) -> Any:
    selector = PC["procedure_projection_selector"]
    return "%s/%d%s" % (selector["collection_pointer_rfc6901"], x.hit.item_index,
                        selector["selected_value_pointer_rfc6901_relative_to_item"])


@derivation("candidate_pointer", "FIRST_UNSELECTED_FORBIDDEN_MEMBER_POINTER")
def _d_unselected_pointer(x: X) -> Any:
    return x.hit.pointer


@derivation("candidate_pointer", "CLAIM_ARTIFACT_PACKAGE_REFERENCE_POINTER")
def _d_package_reference_pointer(x: X) -> Any:
    return "/" + PC["claim_artifacts"][x.subj.claim["candidate_artifact"]]["package_member"]


@derivation("candidate_pointer", "SELECTOR_COLLECTION_POINTER")
def _d_selector_collection_pointer(x: X) -> Any:
    return PC["procedure_projection_selector"]["collection_pointer_rfc6901"]


@derivation("source_identity", "FROZEN_SOURCE_TYPED_IDENTITY")
def _d_frozen_identity(x: X) -> Any:
    return copy.deepcopy(x.subj.frozen["typed_identity"])


@derivation("source_identity", "ACCEPTED_SOURCE_REF_WHEN_VALID_ELSE_NULL")
def _d_accepted_ref(x: X) -> Any:
    return typed_identity(x.subj.row.get("ref") if isinstance(x.subj.row, Mapping) else None)


@derivation("source_identity", "CLAIM_FROZEN_SOURCE_TYPED_IDENTITY_ELSE_NULL")
def _d_claim_frozen_identity(x: X) -> Any:
    tokens = pointer_tokens(x.subj.claim["profile_pointer_rfc6901"])
    if len(tokens) == 2 and tokens[0] == "frozen_authority_pins":
        entry = next((row for row in PC["frozen_sources"] if row["profile_member"] == tokens[1]), None)
        return copy.deepcopy(entry["typed_identity"]) if entry else None
    return None


# --- expected --------------------------------------------------------------
@derivation("expected", "REQUIRED_CALLER_INPUTS")
def _d_required_caller_inputs(x: X) -> Any:
    return [row["input_name"] for row in PC["caller_input_precedence"]
            if row["stage"] == x.fam["stage"] and x.eng.caller_input(row) is None]


@derivation("expected", "VERIFIER_PROFILE_SCHEMA_ID")
def _d_verifier_schema_id(x: X) -> Any:
    return PROFILE_SCHEMA_ID


@derivation("expected", "CALLER_EXPECTED_SHA256", )
def _d_caller_expected_sha_expected(x: X) -> Any:
    return x.eng.profile_schema_expected_sha()


@derivation("expected", "DRAFT_2020_12_DIALECT")
def _d_dialect(x: X) -> Any:
    return DRAFT_2020_12


@derivation("expected", "REQUIRED_MEMBER_JSON_TYPE")
def _d_required_member_type(x: X) -> Any:
    return x.hit.entry["json_type"]


@derivation("expected", "PIN_GIT_BLOB")
def _d_pin_git_blob(x: X) -> Any:
    if x.subj.cls == "FROZEN_SOURCE":
        value = ptr_lookup(x.eng.profile, "/frozen_authority_pins/" + encode_pointer_token(x.subj.frozen["profile_member"])
                           + "/git_blob")
    else:
        value = x.subj.row.get("git_blob", _ABSENT) if isinstance(x.subj.row, Mapping) else _ABSENT
    return None if value is _ABSENT else copy.deepcopy(value)


@derivation("expected", "ALLOWLIST_DIGEST_FIELD")
def _d_allowlist_digest(x: X) -> Any:
    value = x.subj.row.get(x.cond["digest_field"], _ABSENT) if isinstance(x.subj.row, Mapping) else _ABSENT
    return None if value is _ABSENT else copy.deepcopy(value)


@derivation("expected", "PROFILE_CLAIM_VALUE")
def _d_profile_claim_value(x: X) -> Any:
    value = ptr_lookup(x.eng.profile, x.subj.claim["profile_pointer_rfc6901"])
    return None if value is _ABSENT else copy.deepcopy(value)


@derivation("expected", "PROTOCOL_SELECTOR")
def _d_protocol_selector(x: X) -> Any:
    return copy.deepcopy(PC["procedure_projection_selector"])


@derivation("expected", "REQUIRED_MATCH_COUNT")
def _d_required_match_count(x: X) -> Any:
    return PC["procedure_projection_selector"]["selection"]["required_match_count"]


@derivation("expected", "SELECTOR_COLLECTION_TYPE")
def _d_selector_collection_type(x: X) -> Any:
    return PC["procedure_projection_selector"]["collection_type"]


@derivation("expected", "REQUIRED_CONTENT_ROW_MATCH_COUNT")
def _d_required_content_count(x: X) -> Any:
    return FAMILIES["PE-17"]["content_row_matching"]["required_match_count"]


# --- actual ----------------------------------------------------------------
@derivation("actual", "CALLER_SCHEMA_ID")
def _d_caller_schema_id(x: X) -> Any:
    return x.eng.profile_schema_id_value()


@derivation("actual", "COMPUTED_SHA256")
def _d_computed_sha256(x: X) -> Any:
    return sha256(x.eng.profile_schema_raw())


@derivation("actual", "CALLER_EXPECTED_SHA256")
def _d_caller_expected_sha_actual(x: X) -> Any:
    return x.eng.profile_schema_expected_sha()


@derivation("actual", "SCHEMA_DIALECT_MEMBER")
def _d_schema_dialect_member(x: X) -> Any:
    value = x.eng.profile_schema_doc.get("$schema", _ABSENT)
    return None if value is _ABSENT else copy.deepcopy(value)


@derivation("actual", "SCHEMA_ID_MEMBER")
def _d_schema_id_member(x: X) -> Any:
    value = x.eng.profile_schema_doc.get("$id", _ABSENT)
    return None if value is _ABSENT else copy.deepcopy(value)


@derivation("actual", "MEMBER_JSON_TYPE")
def _d_member_json_type(x: X) -> Any:
    return x.hit.actual_type


@derivation("actual", "COMPUTED_GIT_BLOB")
def _d_computed_git_blob(x: X) -> Any:
    return git_blob_id(x.hit.raw)


@derivation("actual", "COMPUTED_DIGEST_FIELD")
def _d_computed_digest_field(x: X) -> Any:
    return sha256(x.hit.raw) if x.cond["digest_field"] == "raw_sha256" else semantic_digest(x.hit.parsed)


@derivation("actual", "CANDIDATE_CLAIM_VALUE")
def _d_candidate_claim_value(x: X) -> Any:
    value = x.hit.candidate_value
    return None if value is _ABSENT else copy.deepcopy(value)


@derivation("actual", "CANDIDATE_SELECTOR")
def _d_candidate_selector(x: X) -> Any:
    value = x.hit.candidate_value
    return None if value is _ABSENT else copy.deepcopy(value)


@derivation("actual", "MATCH_COUNT", "CONTENT_ROW_MATCH_COUNT")
def _d_match_count(x: X) -> Any:
    return x.hit.count


@derivation("actual", "PRESENT_MEMBER")
def _d_present_member(x: X) -> Any:
    return copy.deepcopy(x.hit.value)


@derivation("actual", "COLLECTION_JSON_TYPE")
def _d_collection_json_type(x: X) -> Any:
    return x.hit.actual_type


# --- trust_result ----------------------------------------------------------
@derivation("trust_result", "TRUST_FIELDS_ABSENT_OR_MALFORMED_IN_DECLARED_ORDER")
def _d_trust_fields(x: X) -> Any:
    return x.eng.trust_missing_fields()


@derivation("trust_result", "CALLER_ID_VERSION")
def _d_caller_id_version(x: X) -> Any:
    return {"id": x.eng.trust_input("expected_package_id"), "version": x.eng.trust_input("expected_package_version")}


@derivation("trust_result", "PACKAGE_ID_VERSION")
def _d_package_id_version(x: X) -> Any:
    package = x.eng.package
    members = PC["package_identity_members"]
    return {"id": package[members[0]], "version": package[members[1]]}


@derivation("trust_result", "CALLER_IDENTITY3")
def _d_caller_identity3(x: X) -> Any:
    return {"id": x.eng.trust_input("expected_package_id"), "version": x.eng.trust_input("expected_package_version"),
            "digest": x.eng.trust_input("expected_package_digest")}


@derivation("trust_result", "PACKAGE_IDENTITY3_WITH_RECOMPUTED_DIGEST")
def _d_package_identity3(x: X) -> Any:
    package = x.eng.package
    members = PC["package_identity_members"]
    return {"id": package[members[0]], "version": package[members[1]], "digest": x.eng.package_recomputed_digest()}


# --- map_value_comparison --------------------------------------------------
@derivation("map_value_comparison", "SELECTED_PROCEDURE_ID")
def _d_selected_procedure_id(x: X) -> Any:
    return x.subj.procedure["procedure_id"]


@derivation("map_value_comparison", "DESCRIPTOR_ARGUMENT")
def _d_descriptor_argument(x: X) -> Any:
    return x.subj.descriptor["argument"]


@derivation("map_value_comparison", "DESCRIPTOR_POINTER_TOKENS_AS_RFC6901")
def _d_descriptor_pointer(x: X) -> Any:
    return pointer_of(x.subj.descriptor["pointer_tokens"])


@derivation("map_value_comparison", "DESCRIPTOR_BASELINE_ARGUMENT")
def _d_descriptor_baseline_argument(x: X) -> Any:
    return x.subj.descriptor["baseline"]["argument"]


@derivation("map_value_comparison", "DESCRIPTOR_EXPECTED_LITERALS")
def _d_descriptor_literals(x: X) -> Any:
    return copy.deepcopy(x.subj.descriptor["expected_literals"])


@derivation("map_value_comparison", "BASELINE_STATUS_VALUES")
def _d_baseline_status_values(x: X) -> Any:
    return copy.deepcopy(x.hit.baseline_values)


@derivation("map_value_comparison", "MAP_VALUE")
def _d_map_value(x: X) -> Any:
    return copy.deepcopy(x.hit.map_value)


def derivation_conformance() -> None:
    """Startup proof: every derivation_vocabulary token has exactly one implementation (or a declared constant)."""
    missing = [field + "." + token for field, tokens in DV.items() for token, definition in tokens.items()
               if "constant_value" not in definition and (field, token) not in DERIVE]
    unknown = [field + "." + token for field, token in DERIVE if token not in DV.get(field, {})]
    if missing or unknown:
        raise ModelGap("DERIVATION_VOCABULARY_MISMATCH:" + ",".join(missing + unknown))
    used = {(vocabulary_group(row["witness_contract"], field), rule["derivation"]) for row in MODEL["families"]
            for cond in row["conditions"] for field, rule in _witness_rules(cond)}
    unknown_used = [pair for pair in used if pair[1] not in DV.get(pair[0], {})]
    if unknown_used:
        raise ModelGap("DERIVATION_UNDECLARED:" + repr(unknown_used))


def _witness_rules(cond: Mapping[str, Any]):
    def walk(field: str, rule: Any):
        if not isinstance(rule, Mapping):
            return
        if "derivation" in rule:
            yield field, rule
        for key in ("by_subject_class", "by_case"):
            if key in rule:
                for sub in rule[key].values():
                    yield from walk(field, sub)
    for field, rule in (cond.get("witness") or {}).items():
        yield from walk(field, rule)



# ---------------------------------------------------------------------------
# Engine: the inputs and the lazily evaluated facts the model conditions are defined over.
# ---------------------------------------------------------------------------
DIGEST_POINTER = next(c for c in FAMILIES["PE-13"]["conditions"]
                      if c["condition_id"] == "PACKAGE_SELF_DIGEST_MISMATCH")["section_pointer"]
IDENTITY_MEMBERS = ("kind", "id", "version")


def input_dest(input_name: str) -> str:
    return input_name.lstrip("-").replace("-", "_")


class ClaimArtifact:
    __slots__ = ("status", "doc", "row_index")

    def __init__(self, status: str, doc: Any = None, row_index: int | None = None):
        self.status, self.doc, self.row_index = status, doc, row_index


class Engine:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.root: Path | None = Path(args.root) if args.root is not None else None
        self._ep_status: dict[str, str | None] = {}
        self._ep_raw: dict[str, bytes] = {}
        self._ep_decoded: dict[str, Decoded] = {}
        self._digest: str | None = None
        self._schema_raw: bytes | None = None
        self._schema_read = False
        self.profile_schema_doc: Any = None
        self._profile_raw: bytes | None = None
        self._profile_read = False
        self.profile: Any = None
        self.frozen_content: dict[str, tuple[bytes, Any]] = {}
        self.accepted: dict[int, dict[str, Any]] = {}
        self._claims: dict[str, ClaimArtifact] = {}
        self._paths: dict[str, tuple[str, Any]] = {}
        self._path_decoded: dict[str, Decoded] = {}
        self.metacontract: Any = None
        self.contract: _RegistrationContract | None = None
        self.candidate: list[ResolvedObject] = []
        self.candidate_by_ref: dict[tuple[str, str, str], ResolvedObject] = {}
        self.bound_sources: list[ResolvedObject] = []
        self.bound_by_ref: dict[tuple[str, str, str], ResolvedObject] = {}
        self.universe: list[ResolvedObject] = []
        self.universe_view: Any = None
        self._leap_labels: frozenset[str] | None = None
        _LEAP_SECOND_SOURCE["engine"] = self
        self.eligible_rows: list[tuple[int, Mapping[str, Any]]] = []
        self.selected_item_index: int | None = None
        self.procedure_contexts: dict[str, dict[str, Any]] = {}
        self.reserved_declarations: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
        self.reserved_values: dict[str, Any] = {}
        self.trust: dict[str, Any] | None = None

    # -- caller inputs -------------------------------------------------------
    def caller_input(self, row: Mapping[str, Any]) -> Any:
        return getattr(self.args, input_dest(row["input_name"]), None)

    def trust_input(self, name: str) -> Any:
        return getattr(self.args, name, None)

    def missing_inputs(self, stage: str) -> list[str]:
        return [row["input_name"] for row in PC["caller_input_precedence"]
                if row["stage"] == stage and self.caller_input(row) is None]

    def trust_missing_fields(self) -> list[str]:
        fields = []
        for row in PC["caller_input_precedence"]:
            if row["stage"] != FAMILIES["PE-03"]["stage"]:
                continue
            value = self.caller_input(row)
            bad = not isinstance(value, str) or value == ""
            if not bad and row["input_name"] == "expected_package_digest" and not _HEX_DIGEST.fullmatch(value):
                bad = True
            if bad:
                fields.append(row["input_name"])
        return fields

    # -- entrypoints ---------------------------------------------------------
    def entry_path(self, entry: Mapping[str, Any]) -> Any:
        return getattr(self.args, ENTRYPOINT_CLI_DEST[entry["argument"]], None)

    def entry_absent(self, entry: Mapping[str, Any]) -> bool:
        return self.root is None or self.entry_path(entry) is None

    def entry_condition(self, entry: Mapping[str, Any]) -> str | None:
        name = entry["argument"]
        if name not in self._ep_status:
            try:
                self._ep_raw[name] = read_relative(self.root, self.entry_path(entry))
                self._ep_status[name] = None
            except PathIneligible as exc:
                self._ep_status[name] = exc.condition
        return self._ep_status[name]

    def entry_decoded(self, entry: Mapping[str, Any]) -> Decoded:
        name = entry["argument"]
        if name not in self._ep_decoded:
            self._ep_decoded[name] = strict_decode(self._ep_raw[name])
        return self._ep_decoded[name]

    @property
    def package(self) -> Any:
        return self.entry_decoded(ENTRYPOINTS[0]).value

    @property
    def registry(self) -> Any:
        return self.entry_decoded(ENTRYPOINTS[1]).value

    @property
    def rows(self) -> list[Any]:
        return self.registry["objects"]

    def entrypoint_content_identity(self, entry: Mapping[str, Any]) -> dict[str, str] | None:
        document = self.entry_decoded(entry).value
        if not isinstance(document, Mapping):
            return None
        kind = entry["registered_kind"]
        members = PC["package_identity_members"] if kind == "PACKAGE" else ("object_id", "object_version")
        return typed_identity({"kind": kind, "id": document.get(members[0]), "version": document.get(members[1])})

    def package_recomputed_digest(self) -> str:
        if self._digest is None:
            self._digest = semantic_digest(self.package, [DIGEST_POINTER])
        return self._digest

    # -- profile schema inputs ----------------------------------------------
    def profile_schema_id_value(self) -> Any:
        return self.args.acceptance_profile_schema_id

    def profile_schema_expected_sha(self) -> Any:
        return self.args.acceptance_profile_schema_sha256

    def profile_schema_raw(self) -> bytes | None:
        if not self._schema_read:
            self._schema_read = True
            try:
                self._schema_raw = Path(self.args.acceptance_profile_schema).read_bytes()
            except (OSError, ValueError, TypeError):
                self._schema_raw = None
        return self._schema_raw

    def profile_raw(self) -> bytes | None:
        if not self._profile_read:
            self._profile_read = True
            try:
                self._profile_raw = Path(self.args.verification_input).read_bytes()
            except (OSError, ValueError, TypeError):
                self._profile_raw = None
        return self._profile_raw

    # -- registry lookups ----------------------------------------------------
    def rows_with_identity(self, identity_value: Any) -> list[tuple[int, Mapping[str, Any]]]:
        ident = typed_identity(identity_value)
        if ident is None or not isinstance(self.registry, Mapping) or not isinstance(self.registry.get("objects"), list):
            return []
        return [(index, row) for index, row in enumerate(self.registry["objects"])
                if isinstance(row, Mapping) and all(row.get(member) == ident[member] for member in IDENTITY_MEMBERS)]

    def unique_row(self, identity_value: Any) -> Mapping[str, Any] | None:
        rows = self.rows_with_identity(identity_value)
        return rows[0][1] if len(rows) == 1 else None

    def schema_row(self, ref: Any, eligible_only: bool = False) -> Mapping[str, Any] | None:
        rows = [row for _, row in self.rows_with_identity(ref) if row.get("kind") == "SCHEMA"]
        if len(rows) != 1:
            return None
        if eligible_only and not (rows[0].get("status") == "ACTIVE" and rows[0].get("classification") == "NORMATIVE"):
            return None
        return rows[0]

    def schema_document_id(self, ref: Any) -> Any:
        row = self.schema_row(ref)
        return row.get("schema_document_id") if row is not None else None

    def owning_identity(self, owning: str) -> dict[str, str]:
        return copy.deepcopy(BOOTSTRAP_OBJECTS[owning]["identity"])

    def owning_applied_schema_id(self, owning: str) -> str:
        row = self.unique_row(BOOTSTRAP_OBJECTS[owning]["identity"])
        if row is not None and isinstance(row.get("schema_ref"), Mapping):
            found = self.schema_document_id(row["schema_ref"])
            if isinstance(found, str) and found:
                return found
        return BOOTSTRAP_OBJECTS[owning]["schema_document_id"]

    # -- documents read along registered paths ------------------------------
    def path_document(self, path: Any) -> tuple[str, Any]:
        """(status, value): UNREADABLE (path ineligible or bytes unreadable), UNDECODABLE, or OK with the decoded value."""
        key = path if isinstance(path, str) else "\0" + repr(path)
        if key not in self._paths:
            try:
                raw = read_relative(self.root, path)
            except PathIneligible as exc:
                self._paths[key] = ("UNREADABLE", exc.condition)
            else:
                decoded = strict_decode(raw)
                self._path_decoded[key] = decoded
                self._paths[key] = ("UNDECODABLE", decoded.condition) if decoded.condition else ("OK", decoded.value)
                self._paths[key + "\0raw"] = ("RAW", raw)
        return self._paths[key]

    def path_raw(self, path: str) -> bytes:
        self.path_document(path)
        return self._paths[path + "\0raw"][1]

    def path_decoded(self, path: str) -> Decoded:
        self.path_document(path)
        return self._path_decoded[path]

    def claim_artifact(self, name: str) -> ClaimArtifact:
        if name not in self._claims:
            spec = PC["claim_artifacts"][name]
            if spec["package_member"] is None:
                self._claims[name] = ClaimArtifact("OK", self.package)
            else:
                matches = self.rows_with_identity(self.package.get(spec["package_member"]))
                if len(matches) != 1:
                    self._claims[name] = ClaimArtifact("UNRESOLVED")
                else:
                    status, value = self.path_document(matches[0][1].get("path"))
                    self._claims[name] = ClaimArtifact("OK" if status == "OK" else "UNREADABLE",
                                                       value if status == "OK" else None, matches[0][0])
        return self._claims[name]

    def accepted_source(self, index: int) -> dict[str, Any] | None:
        return self.accepted.get(index)

    # -- eligible rows --------------------------------------------------------
    def compute_eligible_rows(self) -> list[tuple[int, Mapping[str, Any]]]:
        members = PC["eligibility_members_in_order"]
        self.eligible_rows = [(index, row) for index, row in enumerate(self.rows)
                              if isinstance(row, Mapping) and all(row.get(name) == value for name, value in members)]
        return self.eligible_rows

    def load_contract(self) -> "_RegistrationContract":
        if self.contract is None:
            self.contract = registration_contract(REGISTRATION, self.metacontract)
        return self.contract

    # -- governed input of the date-time assertion ---------------------------
    def leap_second_labels(self) -> frozenset[str]:
        """The UTC leap second labels listed by the registered leap-second table of this package.
        metacontract:/runtime_representation/schema_format_assertion/standard_domain_semantics/leap_second_rule names the table
        (table_ref, table_path) and pins its RFC8785 SHA-256 (table_semantic_sha256). The table is read through its registry row
        from the package root, and must be exactly that registered object at exactly that path with exactly that digest; there is
        no embedded copy, no network and no refresh. Anything else fails closed (LeapSecondTableUnavailable): the format
        assertion cannot be made, so no validation outcome is reported."""
        if self._leap_labels is None:
            def unavailable(reason: str):
                raise LeapSecondTableUnavailable("LEAP_SECOND_TABLE_UNAVAILABLE:" + reason)
            rule = ptr_lookup(self.metacontract, "/runtime_representation/schema_format_assertion/standard_domain_semantics/leap_second_rule")
            if not isinstance(rule, Mapping):
                unavailable("RULE_UNDECLARED")
            pin, path = rule.get("table_semantic_sha256"), rule.get("table_path")
            if rule.get("table_digest_algorithm") != "SHA-256" or rule.get("table_digest_serialization") != "RFC8785_JCS":
                unavailable("DIGEST_MODE_UNSUPPORTED")
            if not isinstance(pin, str) or not _HEX_DIGEST.fullmatch(pin) or not isinstance(path, str):
                unavailable("RULE_MALFORMED")
            rows = self.rows_with_identity(rule.get("table_ref"))
            if len(rows) != 1 or rows[0][1].get("path") != path:
                unavailable("TABLE_NOT_REGISTERED_AT_THE_DECLARED_PATH")
            status, document = self.path_document(path)
            if status != "OK":
                unavailable("TABLE_" + status)
            try:
                digest = semantic_digest(document)
            except ExpressionError:
                unavailable("TABLE_NOT_CANONICALIZABLE")
            if digest != pin:
                unavailable("TABLE_DIGEST_DIFFERS_FROM_PIN")
            insertions = document.get("insertions") if isinstance(document, dict) else None
            if not isinstance(insertions, list) or not all(isinstance(row, dict) and isinstance(row.get("utc_instant"), str)
                                                           for row in insertions):
                unavailable("TABLE_SHAPE")
            self._leap_labels = frozenset(row["utc_instant"] for row in insertions)
        return self._leap_labels



# ---------------------------------------------------------------------------
# Family evaluation: subjects, condition predicates and the declared orders.
# ---------------------------------------------------------------------------
GROUP_HANDLERS: dict[tuple[str, ...], Any] = {}


def group_handler(*families: str):
    def register(function):
        GROUP_HANDLERS[tuple(families)] = function
        return function
    return register


def ordered_conditions(family_id: str) -> list[dict[str, Any]]:
    return sorted(FAMILIES[family_id]["conditions"], key=lambda row: row["rank"])


def applies(cond: Mapping[str, Any], subject: Subj) -> bool:
    scope = cond.get("subject_scope")
    return scope is None or subject.cls in scope


def scan(eng: Engine, family_id: str, subjects: Sequence[Subj], predicates: Mapping[str, Any],
         subject_major: bool | None = None) -> None:
    """First failure of one family: the family's declared within_family_order over (condition, subject) pairs."""
    conds = ordered_conditions(family_id)
    if {c["condition_id"] for c in conds} != set(predicates):
        raise ModelGap("CONDITION_PREDICATE_SET_MISMATCH:" + family_id)
    order = FAMILIES[family_id]["within_family_order"]
    if subject_major is None:
        subject_major = order in ("SUBJECT_ORDER_THEN_CONDITION_RANK", "REGISTRATION_DECLARED_ORDER")
    pairs = ((c, s) for s in subjects for c in conds) if subject_major else ((c, s) for c in conds for s in subjects)
    for cond, subject in pairs:
        if not applies(cond, subject):
            continue
        hit = predicates[cond["condition_id"]](subject)
        if hit is not None and hit is not False:
            raise eng.failure(family_id, cond["condition_id"], subject, hit if isinstance(hit, Hit) else Hit())


def scan_subject_major(eng: Engine, group: Mapping[str, Any], subjects: Sequence[Subj],
                       predicates: Mapping[str, Mapping[str, Any]]) -> None:
    """SUBJECT_MAJOR group: (subject index, family_rank_within_subject, condition rank)."""
    rank = group["family_rank_within_subject"]
    families = sorted(group["families"], key=lambda family_id: rank[family_id])
    for family_id in families:
        if {c["condition_id"] for c in FAMILIES[family_id]["conditions"]} != set(predicates[family_id]):
            raise ModelGap("CONDITION_PREDICATE_SET_MISMATCH:" + family_id)
    for subject in subjects:
        for family_id in families:
            if subject.cls not in FAMILIES[family_id]["subject_classes"]:
                continue
            for cond in ordered_conditions(family_id):
                if not applies(cond, subject):
                    continue
                hit = predicates[family_id][cond["condition_id"]](subject)
                if hit is not None and hit is not False:
                    raise eng.failure(family_id, cond["condition_id"], subject, hit if isinstance(hit, Hit) else Hit())


def _engine_failure(self: Engine, family_id: str, condition_id: str, subject: Subj, hit: Hit) -> PreExecFailure:
    return build_failure(self, family_id, condition_id, subject, hit)


Engine.failure = _engine_failure  # type: ignore[attr-defined]


def entry_subjects(eng: Engine, classes: Sequence[str] | None = None) -> list[Subj]:
    subjects = [Subj("ENTRYPOINT_" + entry["registered_kind"], entry=entry) for entry in ENTRYPOINTS]
    return [s for s in subjects if classes is None or s.cls in classes]


# --- stage 0 --------------------------------------------------------------------------------
@group_handler("PE-01")
def _pe01(eng: Engine) -> None:
    scan(eng, "PE-01", entry_subjects(eng), {
        "ENTRYPOINT_INPUT_ABSENT": lambda s: Hit() if eng.entry_absent(s.entry) else None,
    })


@group_handler("PE-03")
def _pe03(eng: Engine) -> None:
    scan(eng, "PE-03", [Subj("CALLER_TRUST_TRIPLE")], {
        "TRUST_TRIPLE_ABSENT_OR_MALFORMED": lambda s: Hit() if eng.trust_missing_fields() else None,
    })


@group_handler("PE-02")
def _pe02(eng: Engine) -> None:
    def condition(token: str):
        return lambda s: Hit() if eng.entry_condition(s.entry) == token else None
    scan(eng, "PE-02", entry_subjects(eng), {
        "ENTRYPOINT_PATH_NOT_CANONICAL": condition("NOT_CANONICAL"),
        "ENTRYPOINT_PATH_OUTSIDE_ROOT": condition("OUTSIDE_ROOT"),
        "ENTRYPOINT_UNREADABLE": condition("UNREADABLE"),
    })


# --- stage 1..4: caller profile schema input ---------------------------------------------------
@group_handler("PE-04")
def _pe04(eng: Engine) -> None:
    stage = FAMILIES["PE-04"]["stage"]
    scan(eng, "PE-04", [Subj("CALLER_PROFILE_SCHEMA_INPUT")], {
        "PROFILE_SCHEMA_INPUT_MISSING": lambda s: Hit() if eng.missing_inputs(stage) else None,
        "PROFILE_SCHEMA_BYTES_UNREADABLE": lambda s: Hit() if eng.profile_schema_raw() is None else None,
    })


@group_handler("PE-06")
def _pe06(eng: Engine) -> None:
    def malformed(_: Subj):
        value = eng.profile_schema_expected_sha()
        return Hit() if not (isinstance(value, str) and _HEX_DIGEST.fullmatch(value)) else None
    scan(eng, "PE-06", [Subj("CALLER_PROFILE_SCHEMA_INPUT")], {"PROFILE_SCHEMA_DIGEST_MALFORMED": malformed})


@group_handler("PE-05")
def _pe05(eng: Engine) -> None:
    scan(eng, "PE-05", [Subj("CALLER_PROFILE_SCHEMA_INPUT")], {
        "CALLER_SCHEMA_ID_NOT_VERIFIER_ID": lambda s: Hit() if eng.profile_schema_id_value() != PROFILE_SCHEMA_ID else None,
    })


@group_handler("PE-07")
def _pe07(eng: Engine) -> None:
    scan(eng, "PE-07", [Subj("CALLER_PROFILE_SCHEMA_INPUT")], {
        "PROFILE_SCHEMA_RAW_DIGEST_MISMATCH":
            lambda s: Hit() if sha256(eng.profile_schema_raw()) != eng.profile_schema_expected_sha() else None,
    })


@group_handler("PE-08")
def _pe08(eng: Engine) -> None:
    decoded = strict_decode(eng.profile_schema_raw())
    document = decoded.value if decoded.condition is None else None
    if isinstance(document, dict):
        eng.profile_schema_doc = document

    def undecodable(_: Subj):
        return Hit() if not isinstance(document, dict) else None

    scan(eng, "PE-08", [Subj("CALLER_PROFILE_SCHEMA_INPUT")], {
        "PROFILE_SCHEMA_UNDECODABLE": undecodable,
        "PROFILE_SCHEMA_DIALECT": lambda s: Hit() if document.get("$schema") != DRAFT_2020_12 else None,
        "PROFILE_SCHEMA_ID": lambda s: Hit() if document.get("$id") != PROFILE_SCHEMA_ID else None,
        "PROFILE_SCHEMA_METASCHEMA": lambda s: Hit() if not metaschema_valid(document) else None,
        "PROFILE_SCHEMA_NONLOCAL_REF": lambda s: Hit() if first_nonlocal_reference(document) is not None else None,
    })


# --- stage 5: entrypoint decode --------------------------------------------------------------
@group_handler("PE-09")
def _pe09(eng: Engine) -> None:
    def condition(token: str):
        return lambda s: Hit() if eng.entry_decoded(s.entry).condition == token else None
    scan(eng, "PE-09", entry_subjects(eng), {
        "ENTRYPOINT_INVALID_UTF8": condition("UTF8"),
        "ENTRYPOINT_JSON_SYNTAX": condition("SYNTAX"),
        "ENTRYPOINT_NUMBER_LIMIT": condition("NUMBER_LIMIT"),
        "ENTRYPOINT_DUPLICATE_NAME": condition("DUPLICATE"),
    })


# --- stage 6: package document, identity, self-integrity, trust, entrypoint binding ----------------
@group_handler("PE-10")
def _pe10(eng: Engine) -> None:
    def identity_invalid(_: Subj):
        package = eng.package
        for member in PC["package_identity_members"]:
            if not nonempty(package.get(member)):
                return Hit(member=member)
        return None
    scan(eng, "PE-10", entry_subjects(eng, ["ENTRYPOINT_PACKAGE"]), {
        "PACKAGE_NOT_OBJECT": lambda s: Hit() if not isinstance(eng.package, dict) else None,
        "PACKAGE_IDENTITY_INVALID": identity_invalid,
    })


@group_handler("PE-12")
def _pe12(eng: Engine) -> None:
    def not_canonicalizable(_: Subj):
        pointer = first_uncanonicalizable_number(eng.package)
        return Hit(pointer=pointer) if pointer is not None else None
    scan(eng, "PE-12", entry_subjects(eng, ["ENTRYPOINT_PACKAGE"]), {"PACKAGE_NOT_RFC8785": not_canonicalizable})


def _constraint_satisfied(constraint: Mapping[str, Any], value: Any) -> bool:
    if "const" in constraint:
        return json_equal(value, constraint["const"])
    if "pattern" in constraint:
        return pattern_matches(constraint["pattern"], value)
    raise ModelGap("PACKAGE_SELF_DIGEST_CONSTRAINT_UNSUPPORTED")


def package_self_digest_location(package: Mapping[str, Any]) -> str | None:
    """PACKAGE_SELF_DIGEST_DECLARATION_LOCATION; None when the declaration satisfies the protocol declaration."""
    declaration = PC["package_self_digest_declaration"]
    section = package.get(declaration["pointer"].lstrip("/"), _ABSENT)
    if not isinstance(section, Mapping):
        return declaration["pointer"]
    for name, constraint in declaration["members_in_declared_order"]:
        value = section.get(name, _ABSENT)
        if value is _ABSENT or not _constraint_satisfied(constraint, value):
            return declaration["pointer"] + "/" + encode_pointer_token(name)
    if set(section) - {name for name, _ in declaration["members_in_declared_order"]}:
        return declaration["pointer"]
    return None


@group_handler("PE-13")
def _pe13(eng: Engine) -> None:
    def declaration_invalid(_: Subj):
        pointer = package_self_digest_location(eng.package)
        return Hit(pointer=pointer) if pointer is not None else None

    def digest_mismatch(_: Subj):
        stored = ptr_lookup(eng.package, DIGEST_POINTER)
        return Hit() if stored != eng.package_recomputed_digest() else None

    scan(eng, "PE-13", entry_subjects(eng, ["ENTRYPOINT_PACKAGE"]), {
        "PACKAGE_SELF_DIGEST_DECLARATION_INVALID": declaration_invalid,
        "PACKAGE_SELF_DIGEST_MISMATCH": digest_mismatch,
    })


@group_handler("PE-11")
def _pe11(eng: Engine) -> None:
    members = PC["package_identity_members"]

    def foreign(_: Subj):
        package = eng.package
        return Hit() if (eng.trust_input("expected_package_id") != package[members[0]]
                         or eng.trust_input("expected_package_version") != package[members[1]]) else None

    def digest(_: Subj):
        return Hit() if eng.trust_input("expected_package_digest") != eng.package_recomputed_digest() else None

    scan(eng, "PE-11", [Subj("TRUST_COMPARISON")], {"FOREIGN_IDENTITY": foreign, "DIGEST": digest})
    package = eng.package
    expected = {"id": eng.trust_input("expected_package_id"), "version": eng.trust_input("expected_package_version"),
                "digest": eng.trust_input("expected_package_digest")}
    eng.trust = {"status": "PASS", "code": "EXPECTED_PACKAGE_VERIFIED", "witness": {
        "stage": "EXACT_TRIPLE_MATCH", "expected": expected,
        "actual": {"id": package[members[0]], "version": package[members[1]], "digest": eng.package_recomputed_digest()}}}


@group_handler("PE-33")
def _pe33(eng: Engine) -> None:
    def registry_not_object(s: Subj):
        registry = eng.registry
        return Hit() if not isinstance(registry, dict) or not isinstance(registry.get("objects"), list) else None

    def package_reference(s: Subj):
        registry, reference = eng.registry, eng.package.get("object_registry_ref")
        expected = {"kind": "REGISTRY", "id": registry.get("object_id"), "version": registry.get("object_version")}
        same = isinstance(reference, Mapping) and all(reference.get(m) == expected[m] for m in IDENTITY_MEMBERS)
        return None if same else Hit()

    def row_not_unique(s: Subj):
        rows = eng.rows_with_identity(eng.entrypoint_content_identity(s.entry))
        return Hit() if len(rows) != 1 else None

    def path_differs(s: Subj):
        rows = eng.rows_with_identity(eng.entrypoint_content_identity(s.entry))
        if len(rows) != 1:
            return None
        return Hit(row_index=rows[0][0]) if rows[0][1].get("path") != eng.entry_path(s.entry) else None

    scan(eng, "PE-33", entry_subjects(eng), {
        "REGISTRY_NOT_OBJECT": registry_not_object, "PACKAGE_REGISTRY_REFERENCE": package_reference,
        "ENTRYPOINT_ROW_NOT_UNIQUE": row_not_unique, "ENTRYPOINT_PATH_DIFFERS": path_differs,
    })


# --- stage 7..8: caller external acceptance profile -------------------------------------------
@group_handler("PE-14")
def _pe14(eng: Engine) -> None:
    stage = FAMILIES["PE-14"]["stage"]
    scan(eng, "PE-14", [Subj("CALLER_PROFILE")], {
        "PROFILE_INPUT_MISSING": lambda s: Hit() if eng.missing_inputs(stage) else None,
        "PROFILE_UNREADABLE": lambda s: Hit() if eng.profile_raw() is None else None,
    })


@group_handler("PE-15")
def _pe15(eng: Engine) -> None:
    decoded = strict_decode(eng.profile_raw())
    eng.profile = decoded.value if decoded.condition is None else None
    schema = eng.profile_schema_doc

    def schema_violation(_: Subj):
        errors = schema_failures(validator_for(schema), eng.profile)
        tokens = first_failure_tokens(errors)
        return Hit(pointer=pointer_of(tokens)) if tokens is not None else None

    def required_member(_: Subj):
        for entry in PC["required_profile_members"]:
            value = ptr_lookup(eng.profile, entry["profile_pointer"])
            token = json_type_token(value)
            if not json_type_satisfies(token, entry["json_type"]):
                return Hit(entry=entry, actual_type=token)
        return None

    scan(eng, "PE-15", [Subj("CALLER_PROFILE")], {
        "PROFILE_UNDECODABLE": lambda s: Hit() if decoded.condition is not None else None,
        "PROFILE_SCHEMA_VIOLATION": schema_violation,
        "PROFILE_REQUIRED_MEMBER": required_member,
    })


# --- stage 9..10: frozen sources --------------------------------------------------------------
def _frozen_handler(family_id: str):
    fam = FAMILIES[family_id]
    frozen = next(row for row in PC["frozen_sources"] if row["profile_member"] == fam["profile_member"])
    member = frozen["profile_member"]

    def handler(eng: Engine) -> None:
        pointer = "/frozen_authority_contents/" + encode_pointer_token(member) + "/content_base64"
        encoded = ptr_lookup(eng.profile, pointer)
        raw = base64_strict(encoded) if encoded is not _ABSENT else None
        pin = ptr_lookup(eng.profile, "/frozen_authority_pins/" + encode_pointer_token(member) + "/git_blob")

        def undecodable(_: Subj):
            return Hit() if strict_decode(raw).condition is not None else None

        scan(eng, family_id, [Subj("FROZEN_SOURCE", frozen=frozen)], {
            "FROZEN_BASE64_INVALID": lambda s: Hit() if raw is None else None,
            "FROZEN_GIT_BLOB": lambda s: Hit(raw=raw) if pin is _ABSENT or git_blob_id(raw) != pin else None,
            "FROZEN_UNDECODABLE": undecodable,
        })
        eng.frozen_content[member] = (raw, strict_decode(raw).value)
    return handler


for _family in ("PE-16A", "PE-16B"):
    GROUP_HANDLERS[(_family,)] = _frozen_handler(_family)


# --- stage 11: accepted sources ---------------------------------------------------------------
def content_row_matches(profile: Mapping[str, Any], allow: Any) -> list[int]:
    matching = FAMILIES["PE-17"]["content_row_matching"]
    rows = ptr_lookup(profile, matching["collection_pointer"])
    if not isinstance(rows, list) or not isinstance(allow, Mapping):
        return []
    found = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        if all(spec["content_row_member"] in row and spec["allowlist_member"] in allow
               and json_equal(row[spec["content_row_member"]], allow[spec["allowlist_member"]])
               for spec in matching["match_members"]):
            found.append(index)
    return found


@group_handler("PE-17")
def _pe17(eng: Engine) -> None:
    allowlist = ptr_lookup(eng.profile, "/accepted_source_allowlist")
    subjects = []
    for index, allow in enumerate(allowlist if isinstance(allowlist, list) else []):
        ref = allow.get("ref") if isinstance(allow, Mapping) else None
        subjects.append(Subj("ALLOWLIST_ROW", index=index, row=allow,
                             ref_kind=ref.get("kind") if isinstance(ref, Mapping) else None))
    facts: dict[int, dict[str, Any]] = {}

    def fact(s: Subj) -> dict[str, Any]:
        if s.index not in facts:
            matches = content_row_matches(eng.profile, s.row)
            record: dict[str, Any] = {"matches": matches}
            if len(matches) == 1:
                row = ptr_lookup(eng.profile, FAMILIES["PE-17"]["content_row_matching"]["collection_pointer"])[matches[0]]
                raw = base64_strict(row.get("content_base64"))
                record["raw"] = raw
                if raw is not None:
                    decoded = strict_decode(raw)
                    record["decoded"] = decoded
                    record["semantic"] = None
                    if decoded.condition is None and not contains_uncanonicalizable_number(decoded.value):
                        record["semantic"] = semantic_digest(decoded.value)
            facts[s.index] = record
        return facts[s.index]

    def cardinality(s: Subj):
        matches = fact(s)["matches"]
        if len(matches) == 1:
            return None
        return Hit(case="ZERO_MATCHING_CONTENT_ROWS" if not matches else "MANY_MATCHING_CONTENT_ROWS", count=len(matches))

    def member(test):
        def predicate(s: Subj):
            record = fact(s)
            if len(record["matches"]) != 1:
                return None
            return test(s, record)
        return predicate

    def base64_invalid(s: Subj, record):
        return Hit(content_index=record["matches"][0]) if record["raw"] is None else None

    def git_blob(s: Subj, record):
        raw = record["raw"]
        if raw is None:
            return None
        allow = s.row
        return Hit(content_index=record["matches"][0], raw=raw) if git_blob_id(raw) != allow.get("git_blob") else None

    def raw_digest(s: Subj, record):
        raw = record["raw"]
        if raw is None:
            return None
        return Hit(content_index=record["matches"][0], raw=raw) if sha256(raw) != s.row.get("raw_sha256") else None

    def undecodable(s: Subj, record):
        if record["raw"] is None:
            return None
        bad = record["decoded"].condition is not None or record["semantic"] is None
        return Hit(content_index=record["matches"][0]) if bad else None

    def semantic_digest_mismatch(s: Subj, record):
        if record["raw"] is None or record["semantic"] is None:
            return None
        if record["semantic"] == s.row.get("semantic_sha256"):
            return None
        return Hit(content_index=record["matches"][0], parsed=record["decoded"].value)

    scan(eng, "PE-17", subjects, {
        "ACCEPTED_CONTENT_ROW_CARDINALITY": cardinality,
        "ACCEPTED_BASE64_INVALID": member(base64_invalid),
        "ACCEPTED_GIT_BLOB": member(git_blob),
        "ACCEPTED_RAW_DIGEST": member(raw_digest),
        "ACCEPTED_UNDECODABLE": member(undecodable),
        "ACCEPTED_SEMANTIC_DIGEST": member(semantic_digest_mismatch),
    })
    for s in subjects:
        record = facts[s.index]
        eng.accepted[s.index] = {"row": s.row, "raw": record["raw"], "parsed": record["decoded"].value,
                                 "content_index": record["matches"][0]}


# --- stage 12: authority claims --------------------------------------------------------------
@group_handler("PE-18")
def _pe18(eng: Engine) -> None:
    claims = [(index, claim) for index, claim in enumerate(PC["claim_comparisons"]) if "candidate_pointer_rfc6901" in claim]
    subjects = [Subj("AUTHORITY_CLAIM", index=index, claim=claim) for index, claim in claims]

    def artifact(s: Subj) -> ClaimArtifact:
        return eng.claim_artifact(s.claim["candidate_artifact"])

    def unresolved(s: Subj):
        found = artifact(s)
        if found.status == "UNRESOLVED":
            return Hit()
        if found.status == "OK" and ptr_lookup(found.doc, s.claim["candidate_pointer_rfc6901"]) is _ABSENT:
            return Hit()
        return None

    def unreadable(s: Subj):
        return Hit() if artifact(s).status == "UNREADABLE" else None

    def mismatch(s: Subj):
        found = artifact(s)
        candidate = ptr_lookup(found.doc, s.claim["candidate_pointer_rfc6901"])
        expected = ptr_lookup(eng.profile, s.claim["profile_pointer_rfc6901"])
        return None if json_equal(candidate, expected) else Hit(candidate_value=candidate)

    scan(eng, "PE-18", subjects, {"CLAIM_ARTIFACT_UNRESOLVED": unresolved, "CLAIM_ARTIFACT_UNREADABLE": unreadable,
                                  "CLAIM_MISMATCH": mismatch})
    eng.metacontract = eng.claim_artifact("metacontract").doc


@group_handler("PE-19")
def _pe19(eng: Engine) -> None:
    claim = next(row for row in PC["claim_comparisons"] if "candidate_selector" in row)
    claim_index = PC["claim_comparisons"].index(claim)
    selector = PC["procedure_projection_selector"]
    selection = selector["selection"]
    subject = Subj("PROCEDURE_PROJECTION_CLAIM", index=claim_index, claim=claim)
    artifact = lambda: eng.claim_artifact(claim["candidate_artifact"])  # noqa: E731
    descriptor = ptr_lookup(eng.profile, claim["profile_pointer_rfc6901"])
    declaration_pointer = "/external_acceptance_profile_contract/candidate_claim_comparisons/%d/candidate_selector" % claim_index
    state: dict[str, Any] = {}

    def selector_unsupported(_: Subj):
        candidate = ptr_lookup(eng.claim_artifact("metacontract").doc, declaration_pointer)
        return None if json_equal(candidate, selector) else Hit(candidate_value=candidate)

    def registry_unresolved(_: Subj):
        return Hit() if artifact().status == "UNRESOLVED" else None

    def registry_unreadable(_: Subj):
        return Hit() if artifact().status == "UNREADABLE" else None

    def classify() -> None:
        if "matches" in state:
            return
        collection = ptr_lookup(artifact().doc, selector["collection_pointer_rfc6901"])
        state["collection"] = collection
        state["matches"] = None
        if isinstance(collection, list):
            state["matches"] = [i for i, item in enumerate(collection)
                                if ptr_lookup(item, selection["member_pointer_rfc6901"]) is not _ABSENT
                                and json_equal(ptr_lookup(item, selection["member_pointer_rfc6901"]), selection["literal"])]

    def match_count(_: Subj):
        classify()
        if state["matches"] is None:
            return Hit(case="COLLECTION_NOT_ARRAY", actual_type=json_type_token(state["collection"]))
        count = len(state["matches"])
        if count == selection["required_match_count"]:
            return None
        return Hit(case="MATCH_COUNT_ZERO" if count == 0 else "MATCH_COUNT_MANY", count=count)

    def selected_descriptor(_: Subj):
        classify()
        index = state["matches"][0]
        value = ptr_lookup(state["collection"][index], selector["selected_value_pointer_rfc6901_relative_to_item"])
        if value is not _ABSENT and json_equal(value, descriptor):
            return None
        return Hit(case="MATCH_COUNT_ONE", item_index=index, candidate_value=value)

    def other_projection(_: Subj):
        classify()
        forbidden = selector["other_items_constraint"]["forbidden_pointer_rfc6901_relative_to_item"]
        selected = set(state["matches"])
        for index, item in enumerate(state["collection"]):
            if index in selected:
                continue
            value = ptr_lookup(item, forbidden)
            if value is not _ABSENT:
                return Hit(case="MATCH_COUNT_ONE", pointer="%s/%d%s" % (selector["collection_pointer_rfc6901"], index, forbidden),
                           value=value)
        return None

    # conditions 5 and 6 are defined only when exactly one item matched (input_cases MATCH_COUNT_ONE)
    scan(eng, "PE-19", [subject], {
        "SELECTOR_UNSUPPORTED": selector_unsupported, "PROCEDURE_REGISTRY_UNRESOLVED": registry_unresolved,
        "PROCEDURE_REGISTRY_UNREADABLE": registry_unreadable, "SELECTOR_MATCH_COUNT": match_count,
        "SELECTED_DESCRIPTOR": selected_descriptor, "OTHER_PROCEDURE_PROJECTION": other_projection})
    eng.selected_item_index = state["matches"][0]



# --- stage 13: verifier protocol declarations and registry structural application -------------------
def group_of(*families: str) -> dict[str, Any]:
    for stage in MODEL["stage_ordering"]:
        for group in stage["groups"]:
            if tuple(group["families"]) == tuple(families):
                return group
    raise ModelGap("GROUP_UNDECLARED:" + ",".join(families))


def _section_digest_differs(metacontract: Any, pointer: str) -> bool:
    section = ptr_lookup(metacontract, pointer)
    if section is _ABSENT:
        return True
    try:
        digest = sha256(jcs_bytes(section))
    except ExpressionError:
        return True
    return digest != PROTOCOL_DIGESTS[pointer.rsplit("/", 1)[1]]


@group_handler("PE-22")
def _pe22(eng: Engine) -> None:
    structural = REGISTRATION["structural_application"]

    def protocol_section(cond_id: str):
        pointer = next(c for c in FAMILIES["PE-22"]["conditions"] if c["condition_id"] == cond_id)["section_pointer"]
        return lambda s: Hit() if _section_digest_differs(eng.metacontract, pointer) else None

    def schema_unavailable(_: Subj):
        rows = eng.rows_with_identity(structural["schema_ref"])
        if not rows:
            return Hit(case="ZERO_MATCHING_ROWS", identity=None)
        if len(rows) > 1:
            return Hit(case="MULTIPLE_MATCHING_ROWS", identity=None)
        row = rows[0][1]
        status, document = eng.path_document(row.get("path"))
        # Declared condition text: "unreadable" is exactly (path not canonical, outside the root, or bytes unreadable).
        # Bytes that were read but do not strictly decode, are not a JSON object, or carry a different $id are the
        # UNIQUE_ROW_READABLE input case; metaschema validity is not part of this condition (it belongs to PE-37).
        if status == "UNREADABLE":
            return Hit(case="UNIQUE_ROW_UNREADABLE", identity=None)
        if status != "OK" or not isinstance(document, dict) or document.get("$id") != structural["schema_id"]:
            return Hit(case="UNIQUE_ROW_READABLE", identity=typed_identity(row))
        return None

    scan(eng, "PE-22", [Subj("PROTOCOL_SECTION"), Subj("REGISTRY_SCHEMA_DECLARATION")], {
        "FAILURE_MODEL_UNSUPPORTED": protocol_section("FAILURE_MODEL_UNSUPPORTED"),
        "REGISTRATION_UNSUPPORTED": protocol_section("REGISTRATION_UNSUPPORTED"),
        "REGISTRY_SCHEMA_UNAVAILABLE": schema_unavailable,
    })


@group_handler("PE-21")
def _pe21(eng: Engine) -> None:
    structural = REGISTRATION["structural_application"]
    schema_document = eng.path_document(eng.unique_row(structural["schema_ref"]).get("path"))[1]
    errors = schema_failures(validator_for(schema_document, registered=True), eng.registry)
    row_errors: dict[int, list[Any]] = {}
    registry_errors: list[Any] = []
    for error in errors:
        path = list(error.absolute_path)
        if len(path) >= 2 and path[0] == "objects" and isinstance(path[1], int) and not isinstance(path[1], bool):
            row_errors.setdefault(path[1], []).append(error)
        else:
            registry_errors.append(error)
    if registry_errors:
        tokens = first_failure_tokens(registry_errors)
        raise eng.failure("PE-21", "OBJECT_REGISTRY_DOCUMENT_LEVEL_SCHEMA_VIOLATION", Subj("REGISTRY_DOCUMENT"),
                          Hit(pointer=pointer_of(tokens)))
    for index in sorted(row_errors):
        row = eng.rows[index]
        subject = Subj("REGISTRY_ROW", index=index, row=row)
        mapping = isinstance(row, Mapping)
        if (mapping and row.get("status") == "ACTIVE" and row.get("classification") == "NORMATIVE"
                and "kind" in row and row.get("kind") != "SCHEMA" and "schema_ref" not in row):
            condition = "MISSING_REGISTRATION_SCHEMA_REF"
        elif mapping and "integrity" not in row:
            condition = "MISSING_REGISTRATION_INTEGRITY_DECLARATION"
        elif mapping and not (isinstance(row["integrity"], Mapping) and isinstance(row["integrity"].get("mode"), str)):
            condition = "MALFORMED_REGISTRATION_INTEGRITY_DECLARATION"
        else:
            condition = "OBJECT_REGISTRY_SCHEMA_VIOLATION"
        raise eng.failure("PE-21", condition, subject, Hit())


# --- stage 14..15: semantic registration and global uniqueness ---------------------------------------
def registry_row_subjects(eng: Engine) -> list[Subj]:
    return [Subj("REGISTRY_ROW", index=index, row=row) for index, row in enumerate(eng.rows) if isinstance(row, Mapping)]


@group_handler("PE-23")
def _pe23(eng: Engine) -> None:
    contract = eng.load_contract()
    evaluation = _RegistrationEvaluation(eng, eng.registry)
    by_rule = {rule.rule_id: rule for rule in contract.rules}
    if set(by_rule) != {c["condition_id"] for c in FAMILIES["PE-23"]["conditions"]}:
        raise ModelGap("PE23_RULE_SET_MISMATCH")

    def predicate(rule: "_RegistrationRule"):
        def test(s: Subj):
            if not rule.applies_to(s.row):
                return None
            outcome = rule.comparator(evaluation, s.row)
            if outcome is False or outcome is None:
                return None
            return Hit(member_index=outcome.member_index if isinstance(outcome, _MemberBindingFault) else "")
        return test
    scan(eng, "PE-23", registry_row_subjects(eng), {rule_id: predicate(rule) for rule_id, rule in by_rule.items()})


@group_handler("PE-24")
def _pe24(eng: Engine) -> None:
    members = REGISTRATION["global_uniqueness"]["identity_key_members"]
    keys: list[tuple[str, ...] | None] = []
    for row in eng.rows:
        values = tuple(row.get(member) for member in members) if isinstance(row, Mapping) else ()
        keys.append(values if values and all(nonempty(value) for value in values) else None)
    for second in range(len(keys)):
        if keys[second] is None:
            continue
        for first in range(second):
            if keys[first] == keys[second]:
                raise eng.failure("PE-24", "DUPLICATE_IDENTITY",
                                  Subj("REGISTRY_DUPLICATE_SELECTION", first=first, second=second, row=eng.rows[second]), Hit())


# --- stage 16: registry integrity declarations ----------------------------------------------------
def integrity_scope_mode(row: Mapping[str, Any]) -> str | None:
    """The mode of a row whose declaration and digest are verified at VERIFY_REGISTRY_INTEGRITY_DECLARATIONS."""
    integrity = row.get("integrity")
    if not (row.get("status") == "ACTIVE" and row.get("classification") == "NORMATIVE" and isinstance(integrity, Mapping)):
        return None
    mode = integrity.get("mode")
    return mode if mode in ("SEMANTIC_JSON_CONTENT", "PACKAGE_PINNED_BOOTSTRAP") else None


@group_handler("PE-25", "PE-27", "PE-26")
def _stage16(eng: Engine) -> None:
    gate = REGISTRATION["integrity_gate"]

    def invalid_mode(s: Subj):
        integrity = s.row.get("integrity")
        if isinstance(integrity, Mapping) and isinstance(integrity.get("mode"), str):
            return Hit() if integrity["mode"] not in gate["declared_mode_must_be_in"] else None
        return None

    def shape_invalid(s: Subj):
        if integrity_scope_mode(s.row) is None:
            return None
        resolved = ptr_lookup(eng.metacontract, "/runtime_representation/value_schemas/resolved_object")
        shape = ptr_lookup(resolved, "/$defs/integrity")
        if shape is _ABSENT:
            return None
        errors = schema_failures(validator_for(shape, resolved), s.row["integrity"])
        tokens = first_failure_tokens(errors)
        return Hit(tokens=tokens) if tokens is not None else None

    def content_of(s: Subj):
        if integrity_scope_mode(s.row) is None:
            return _ABSENT
        status, value = eng.path_document(s.row.get("path"))
        return value if status == "OK" else _ABSENT

    def not_canonicalizable(s: Subj):
        value = content_of(s)
        return Hit() if value is not _ABSENT and contains_uncanonicalizable_number(value) else None

    def digest_mismatch(s: Subj):
        value = content_of(s)
        if value is _ABSENT or contains_uncanonicalizable_number(value):
            return None
        mode = integrity_scope_mode(s.row)
        declared = s.row["integrity"].get("digest") if mode == "SEMANTIC_JSON_CONTENT" else eng.package.get("registry_semantic_sha256")
        return Hit() if semantic_digest(value) != declared else None

    scan_subject_major(eng, group_of("PE-25", "PE-27", "PE-26"), registry_row_subjects(eng), {
        "PE-25": {"INVALID_MODE": invalid_mode},
        "PE-27": {"MODE_SHAPE_INVALID": shape_invalid},
        "PE-26": {"CONTENT_NOT_RFC8785": not_canonicalizable, "DIGEST_MISMATCH": digest_mismatch},
    })


# --- stage 17: bootstrap object eligibility ------------------------------------------------------
@group_handler("PE-33B")
def _pe33b(eng: Engine) -> None:
    subjects = []
    for bootstrap in PC["bootstrap_objects"]:
        if bootstrap["package_member"] is None:
            identity_value = eng.entrypoint_content_identity(ENTRYPOINTS[0])
        else:
            identity_value = eng.package.get(bootstrap["package_member"])
        subjects.append(Subj("BOOTSTRAP_OBJECT", bootstrap=bootstrap, identity=identity_value))
    cases = {"status": "ROW_STATUS_NOT_ACTIVE", "classification": "ROW_CLASSIFICATION_NOT_NORMATIVE"}

    def not_eligible(s: Subj):
        rows = eng.rows_with_identity(s.identity)
        if len(rows) != 1:
            return Hit(case="ROW_ABSENT_OR_NOT_UNIQUE", row=None)
        index, row = rows[0]
        for member, expected in PC["eligibility_members_in_order"]:
            if row.get(member) != expected:
                return Hit(case=cases[member], row_index=index, row=row)
        return None
    scan(eng, "PE-33B", subjects, {"BOOTSTRAP_NOT_ELIGIBLE": not_eligible})
    eng.compute_eligible_rows()


# --- stage 18: resolve candidate objects ------------------------------------------------------------
@group_handler("PE-30", "PE-31", "PE-32")
def _stage18(eng: Engine) -> None:
    subjects = [Subj("ELIGIBLE_SCHEMA_ROW" if row.get("kind") == "SCHEMA" else "ELIGIBLE_NON_SCHEMA_ROW", index=index, row=row)
                for index, row in eng.eligible_rows]

    def path_condition(token: str):
        def test(s: Subj):
            status, detail = eng.path_document(s.row.get("path"))
            return Hit() if status == "UNREADABLE" and detail == token else None
        return test

    def decode_condition(token: str):
        def test(s: Subj):
            status, detail = eng.path_document(s.row.get("path"))
            return Hit() if status == "UNDECODABLE" and detail == token else None
        return test

    def not_object(s: Subj):
        status, value = eng.path_document(s.row.get("path"))
        return Hit() if status == "OK" and not isinstance(value, dict) else None

    scan_subject_major(eng, group_of("PE-30", "PE-31", "PE-32"), subjects, {
        "PE-30": {"OBJECT_PATH_NOT_CANONICAL": path_condition("NOT_CANONICAL"),
                  "OBJECT_PATH_OUTSIDE_ROOT": path_condition("OUTSIDE_ROOT"),
                  "OBJECT_UNREADABLE": path_condition("UNREADABLE")},
        "PE-31": {"OBJECT_INVALID_UTF8": decode_condition("UTF8"), "OBJECT_JSON_SYNTAX": decode_condition("SYNTAX"),
                  "OBJECT_NUMBER_LIMIT": decode_condition("NUMBER_LIMIT"),
                  "OBJECT_DUPLICATE_NAME": decode_condition("DUPLICATE")},
        "PE-32": {"OBJECT_NOT_JSON_OBJECT": not_object},
    })


# --- stage 19: bound source resolved construction (vector registry claim) -----------------------------
def vector_claim_witness(x: X) -> dict[str, Any]:
    hit, allow = x.hit, x.subj.row
    ref = allow["ref"]
    witness: dict[str, Any] = {
        "source_kind": ref["kind"], "source_id": ref["id"], "source_version": ref["version"],
        "source_origin": "BOUND_SOURCE_UNIVERSE", "source_path": allow["canonical_path"],
        "registry_claim_key": {member: ref[member] for member in IDENTITY_MEMBERS},
        "match_count": hit.count, "reason": hit.reason, "diagnostic": x.cond["diagnostic"]}
    for name in ("missing_member_ids", "extra_member_ids", "duplicate_member_ids"):
        if name in hit.__dict__ and hit.__dict__[name] is not None:
            witness[name] = hit.__dict__[name]
    return witness


def _utf16_sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted(set(values), key=utf16_key)


def _duplicates(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        (repeated if value in seen else seen).add(value)
    return _utf16_sorted_unique(repeated)


@group_handler("PE-34")
def _pe34(eng: Engine) -> None:
    allowlist = ptr_lookup(eng.profile, "/accepted_source_allowlist")
    index = next((i for i, allow in enumerate(allowlist)
                  if isinstance(allow.get("ref"), Mapping) and allow["ref"].get("kind") == "SOURCE_VECTOR_CATALOG"), None)
    if index is None:
        return
    allow = allowlist[index]
    ref = allow["ref"]
    subject = Subj("BOUND_VECTOR_SOURCE", index=index, row=allow)
    order = REGISTRATION["bound_source_resolved_construction"]["member_relation"]["failure_ordering"]

    def claim_invalid(_: Subj):
        matches = [row for row in eng.rows if isinstance(row, Mapping) and isinstance(row.get("reference"), Mapping)
                   and all(row["reference"].get(member) == ref[member] for member in IDENTITY_MEMBERS)]
        count = len(matches)
        if count == 0:
            return Hit(reason=order[0], count=0)
        claim = matches[0].get("members")
        if not isinstance(claim, list) or not all(nonempty(item) for item in claim):
            return Hit(reason=order[1], count=count)
        claim_duplicates = _duplicates(claim)
        if claim_duplicates:
            return Hit(reason=order[2], count=count, duplicate_member_ids=claim_duplicates)
        vectors = ptr_lookup(eng.accepted[index]["parsed"], "/vectors")
        if not isinstance(vectors, list) or not all(isinstance(v, Mapping) and nonempty(v.get("vector_id")) for v in vectors):
            return Hit(reason=order[3], count=count)
        derived = [v["vector_id"] for v in vectors]
        content_duplicates = _duplicates(derived)
        if content_duplicates:
            return Hit(reason=order[4], count=count, duplicate_member_ids=content_duplicates)
        if set(claim) != set(derived):
            return Hit(reason=order[5], count=count,
                       missing_member_ids=_utf16_sorted_unique(set(derived) - set(claim)),
                       extra_member_ids=_utf16_sorted_unique(set(claim) - set(derived)))
        return None
    scan(eng, "PE-34", [subject], {"VECTOR_REGISTRY_CLAIM_INVALID": claim_invalid})



# --- stage 20: derive the verification universe (no family: nothing here can fail) ---------------------
def derive_universe(eng: Engine) -> None:
    candidate: list[ResolvedObject] = []
    for index, row in eng.eligible_rows:
        path = row["path"]
        candidate.append(ResolvedObject(ident_record(row["kind"], row["id"], row["version"]), row,
                                        eng.path_document(path)[1], eng.path_raw(path), path, "CANDIDATE_UNIVERSE"))
    bound: list[ResolvedObject] = []
    allowlist = ptr_lookup(eng.profile, "/accepted_source_allowlist")
    for index, allow in enumerate(allowlist):
        record = eng.accepted[index]
        ref, parsed, raw = allow["ref"], record["parsed"], record["raw"]
        members = (_utf16_sorted_unique(v["vector_id"] for v in parsed.get("vectors", [])
                                        if isinstance(v, Mapping) and nonempty(v.get("vector_id")))
                   if ref.get("kind") == "SOURCE_VECTOR_CATALOG" and isinstance(parsed, dict) else [])
        registration = {
            "kind": ref.get("kind"), "id": ref.get("id"), "version": ref.get("version"), "reference": dict(ref),
            "path": allow.get("canonical_path"), "status": allow.get("status"),
            "classification": allow.get("classification"),
            "roles": list(allow["roles"]) if isinstance(allow.get("roles"), list) else [],
            "schema_ref": allow.get("expected_schema_ref"), "members": members,
            "integrity": {"mode": "DUAL_ACCEPTED_SOURCE", "algorithm": "SHA-256", "raw_sha256": sha256(raw),
                          "semantic_sha256": semantic_digest(parsed), "git_blob": git_blob_id(raw)}}
        bound.append(ResolvedObject(dict(ref), registration, parsed, raw, str(allow.get("canonical_path")),
                                    "BOUND_SOURCE_UNIVERSE"))
    eng.candidate, eng.bound_sources = candidate, bound
    eng.candidate_by_ref = {identity(obj.ref): obj for obj in candidate}
    eng.bound_by_ref = {identity(obj.ref): obj for obj in bound}
    eng.universe = sorted(candidate + bound, key=lambda obj: tuple(utf16_key(part) for part in identity(obj.ref)))
    eng.universe_view = {"objects": [obj.public_record() for obj in eng.universe]}
    content = eng.candidate_by_ref.get(identity(eng.package.get("metacontract_ref", {})))
    if content is not None:
        eng.metacontract = content.content


# --- stage 21 group 1: strict identity union collision -----------------------------------------------
def strict_union_witness(x: X) -> dict[str, Any]:
    candidate, bound = x.subj.candidate, x.subj.bound
    return {"kind": candidate.ref["kind"], "id": candidate.ref["id"], "version": candidate.ref["version"],
            "candidate_origin": candidate.source_universe, "candidate_path_or_source": candidate.canonical_path,
            "bound_origin": bound.source_universe, "bound_path_or_source": bound.canonical_path}


@group_handler("PE-35")
def _pe35(eng: Engine) -> None:
    candidate_order = sorted(eng.candidate, key=lambda obj: tuple(utf16_key(part) for part in identity(obj.ref)))
    merged = [(False, obj) for obj in candidate_order] + [(True, obj) for obj in eng.bound_sources]
    for later in range(len(merged)):
        for earlier in range(later):
            if merged[earlier][0] != merged[later][0] and identity(merged[earlier][1].ref) == identity(merged[later][1].ref):
                first, second = merged[earlier], merged[later]
                candidate = first[1] if not first[0] else second[1]
                bound = first[1] if first[0] else second[1]
                raise eng.failure("PE-35", "CROSS_SET_COLLISION", Subj("UNION_COLLISION", candidate=candidate, bound=bound), Hit())


# --- stage 21 group 2: candidate schema documents and candidate object content ---------------------------
def _validation_errors(validator: Any, instance: Any) -> list[Any] | None:
    """All failures when the instance is invalid, else None (the cheap first-error probe precedes the full pass)."""
    if next(validator.iter_errors(instance), None) is None:
        return None
    return list(validator.iter_errors(instance))


# PE-36 content validation, bounded implementation of the SAME question. PE-36 asks whether a governed object satisfies its
# registered Draft 2020-12 schema and where the first failure lies (DESCENDANTS canonical preorder over the locations of the
# top-level failures). pe36_schema_failures answers it with the library's own keyword code and changes only HOW two keywords
# reach their answer:
#   oneOf  The library enumerates every failing branch exhaustively and builds failure contexts nothing here reads (a
#          branch that names an operand slot re-validates the whole operand subtree even though its `op` already fails,
#          so a recursive expression grammar costs exponential time in its depth). Branch validity is a yes/no question,
#          so it is decided at the branch's first failure; the single failure at the oneOf instance (no branch valid, or
#          more than one valid) is the one the library yields.
#   $ref   To a self-referential target (an expression grammar), "instance X satisfies target T" is a pure function of
#          (X, T) when the schema has no dynamic-scope keywords. It is computed once per node, innermost node first, on an
#          explicit stack: no repeated subtree validation and no Python recursion through the grammar, hence no depth bound.
# A schema outside that guard (dynamic-scope keywords, not an object) is validated by the unchanged routine above.
_PE36_DYNAMIC_SCOPE_KEYWORDS = ("$dynamicRef", "$dynamicAnchor", "$recursiveRef", "$recursiveAnchor")


def _pe36_dynamic_scope_free(schema: Any) -> bool:
    stack = [schema]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    stack.append(value)
                elif key in _PE36_DYNAMIC_SCOPE_KEYWORDS:
                    return False
        elif isinstance(node, list):
            stack.extend(item for item in node if isinstance(item, (dict, list)))
    return True


class _Pe36Walk:
    """One PE-36 validation: validity memo of self-referential $ref targets, the explicit-stack interface (driving,
    pending) and the nesting depth of oneOf branch checks (only existence of a failure matters there)."""

    __slots__ = ("memo", "recursive", "pending", "driving", "validity_only")

    def __init__(self) -> None:
        self.memo: dict[tuple[int, int], tuple[Any, bool]] = {}
        self.recursive: dict[int, bool] = {}
        self.pending: dict[tuple[int, int], tuple[Any, Any, Any]] = {}
        self.driving = False
        self.validity_only = 0


def _pe36_validator(schema: Mapping[str, Any]) -> Any:
    walk = _Pe36Walk()
    library = jsonschema.Draft202012Validator
    library_ref = library.VALIDATORS["$ref"]
    failure = jsonschema.ValidationError

    def self_recursive(resolved: Any) -> bool:
        """Does a $ref inside the resolved target resolve back to that same target (a self-referential grammar)?"""
        target = resolved.contents
        if not isinstance(target, dict):
            return False
        found = False
        stack = [target]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        stack.append(value)
                    elif key == "$ref" and isinstance(value, str) and not found:
                        try:
                            found = resolved.resolver.lookup(value).contents is target
                        except Exception:
                            return False
            elif isinstance(node, list):
                stack.extend(item for item in node if isinstance(item, (dict, list)))
        return found

    def resolve(key: tuple[int, int], validator: Any, resolved: Any, instance: Any) -> bool:
        """Validity of `instance` against a self-referential target. A node is evaluated with its operand nodes assumed
        valid; when that evaluation met operand nodes of unknown validity they are resolved first (innermost first) and the
        node is evaluated again, so a recorded answer never rests on an assumption."""
        outer = (walk.driving, walk.pending)
        stack = [(key, validator, resolved, instance)]
        awaiting: set[tuple[int, int]] = set()
        try:
            while stack:
                top_key, top_validator, top_resolved, node = stack[-1]
                if top_key in walk.memo:
                    stack.pop()
                    continue
                walk.driving, walk.pending = True, {}
                holds = next(top_validator.descend(node, top_resolved.contents, resolver=top_resolved.resolver),
                             None) is None
                waiting = walk.pending
                if not waiting:
                    walk.memo[top_key] = (node, holds)
                    awaiting.discard(top_key)
                    stack.pop()
                    continue
                awaiting.add(top_key)
                for child_key in reversed(list(waiting)):
                    if child_key in awaiting:
                        raise RecursionError("$ref chain without instance descent")
                    stack.append((child_key,) + waiting[child_key])
        finally:
            walk.driving, walk.pending = outer
        return walk.memo[key][1]

    def ref_keyword(validator: Any, ref: Any, instance: Any, subschema: Any):
        if validator._ref_resolver is not None:
            yield from library_ref(validator, ref, instance, subschema)
            return
        try:
            resolved = validator._resolver.lookup(ref)
        except Exception:
            yield from library_ref(validator, ref, instance, subschema)  # raises exactly as the library does
            return
        target = resolved.contents
        shared = walk.recursive.get(id(target))
        if shared is None:
            shared = walk.recursive[id(target)] = self_recursive(resolved)
        if not shared:
            yield from validator.descend(instance, target, resolver=resolved.resolver)
            return
        key = (id(target), id(instance))
        known = walk.memo.get(key)
        if known is None:
            if walk.driving:
                walk.pending.setdefault(key, (validator, resolved, instance))
                return
            holds = resolve(key, validator, resolved, instance)
        else:
            holds = known[1]
        if holds:
            return
        if walk.driving or walk.validity_only:
            yield failure("is not valid under the self-referential schema")
        else:
            yield from validator.descend(instance, target, resolver=resolved.resolver)

    def one_of_keyword(validator: Any, one_of: Any, instance: Any, subschema: Any):
        walk.validity_only += 1
        try:
            branches = enumerate(one_of)
            matched = False
            for index, branch in branches:
                if next(validator.descend(instance, branch, schema_path=index), None) is None:
                    matched = True
                    break
            others = ([each for _, each in branches if validator.evolve(schema=each).is_valid(instance)]
                      if matched else [])
        finally:
            walk.validity_only -= 1
        if not matched:
            yield failure("is not valid under any of the given schemas")
        elif others:
            yield failure("is valid under more than one of the given schemas")

    return jsonschema.validators.extend(library, {"$ref": ref_keyword, "oneOf": one_of_keyword})(schema, format_checker=DATE_TIME_FORMAT_CHECKER)


def pe36_schema_failures(schema: Any, instance: Any) -> list[Any]:
    """Top-level JSON Schema failures of `instance` against `schema`: the same validity and the same failure locations as
    list(Draft202012Validator(schema).iter_errors(instance)); first_failure_tokens() consumes only those locations."""
    if not isinstance(schema, dict) or not _pe36_dynamic_scope_free(schema):
        return _validation_errors(validator_for(schema, registered=True), instance) or []
    return list(_pe36_validator(schema).iter_errors(instance))


class _SchemaDefects:
    """PE-37 conditions per eligible SCHEMA row, evaluated once."""

    def __init__(self, eng: Engine):
        self.eng = eng
        self.cache: dict[int, tuple[str, Hit] | None] = {}

    def defect(self, index: int, row: Mapping[str, Any]) -> tuple[str, Hit] | None:
        if index not in self.cache:
            document = self.eng.path_document(row["path"])[1]
            found: tuple[str, Hit] | None = None
            if document.get("$schema") != DRAFT_2020_12:
                found = ("SCHEMA_DIALECT", Hit())
            elif not metaschema_valid(document):
                found = ("SCHEMA_METASCHEMA", Hit(pointer=pointer_of(metaschema_first_failure_tokens(document) or [])))
            else:
                pointer = first_nonlocal_reference(document)
                if pointer is not None:
                    found = ("SCHEMA_NONLOCAL_REF", Hit(pointer=pointer))
            self.cache[index] = found
        return self.cache[index]


def _member_unregistered(schema_row: Mapping[str, Any], ref: Mapping[str, Any]) -> bool:
    member = ref.get("member_id")
    if member is None:
        return False
    members = schema_row.get("members")
    return not isinstance(members, list) or sum(1 for item in members if item == member) != 1


@group_handler("PE-37", "PE-36")
def _stage21_group2(eng: Engine) -> None:
    contract = eng.load_contract()
    schema_map = {key: obj for key, obj in eng.candidate_by_ref.items() if obj.registration.get("kind") == "SCHEMA"}
    defects = _SchemaDefects(eng)
    index_of = {identity(row): index for index, row in eng.eligible_rows}

    def schema_condition(cond_id: str):
        def test(s: Subj):
            found = defects.defect(s.index, s.row)
            return found[1] if found is not None and found[0] == cond_id else None
        return test

    def applied_row(s: Subj):
        return eng.schema_row(s.row.get("schema_ref"))

    def not_in_universe(s: Subj):
        found = applied_row(s)
        return Hit() if found is None or not (found.get("status") == "ACTIVE" and found.get("classification") == "NORMATIVE") else None

    def document_ineligible(s: Subj):
        found = applied_row(s)
        return Hit() if defects.defect(index_of[identity(found)], found) is not None else None

    def member_unregistered(s: Subj):
        return Hit() if _member_unregistered(applied_row(s), s.row["schema_ref"]) else None

    def content_violation(s: Subj):
        obj = eng.candidate_by_ref[identity(s.row)]
        try:
            schema = load_schema_ref(schema_map, s.row["schema_ref"], contract.member_law)
        except ExpressionError:
            return Hit(pointer="")
        errors = pe36_schema_failures(schema, obj.content)
        tokens = first_failure_tokens(errors) if errors else None
        return Hit(pointer=pointer_of(tokens)) if tokens is not None else None

    subjects = [Subj("ELIGIBLE_SCHEMA_ROW" if row.get("kind") == "SCHEMA" else "ELIGIBLE_NON_SCHEMA_ROW", index=index, row=row)
                for index, row in eng.eligible_rows]
    scan_subject_major(eng, group_of("PE-37", "PE-36"), subjects, {
        "PE-37": {"SCHEMA_DIALECT": schema_condition("SCHEMA_DIALECT"), "SCHEMA_METASCHEMA": schema_condition("SCHEMA_METASCHEMA"),
                  "SCHEMA_NONLOCAL_REF": schema_condition("SCHEMA_NONLOCAL_REF")},
        "PE-36": {"APPLIED_SCHEMA_NOT_IN_UNIVERSE": not_in_universe,
                  "APPLIED_SCHEMA_DOCUMENT_INELIGIBLE": document_ineligible,
                  "APPLIED_SCHEMA_MEMBER_UNREGISTERED": member_unregistered,
                  "CONTENT_SCHEMA_VIOLATION": content_violation},
    })


# --- stage 21 group 3: bound source content ------------------------------------------------------------
def resolve_expected_schema(eng: Engine, ref: Any) -> tuple[str | None, Mapping[str, Any] | None]:
    """(unresolved case, eligible SCHEMA row): the row exists and, when named, its member is registered."""
    row = eng.schema_row(ref, eligible_only=True)
    if row is None:
        return "EXPECTED_SCHEMA_ROW_UNRESOLVED", None
    if isinstance(ref, Mapping) and _member_unregistered(row, ref):
        return "EXPECTED_SCHEMA_MEMBER_UNREGISTERED", None
    return None, row


@group_handler("PE-38")
def _pe38(eng: Engine) -> None:
    contract = eng.load_contract()
    schema_map = {key: obj for key, obj in eng.candidate_by_ref.items() if obj.registration.get("kind") == "SCHEMA"}
    allowlist = ptr_lookup(eng.profile, "/accepted_source_allowlist")
    subjects = [Subj("BOUND_SOURCE", index=index, row=allow) for index, allow in enumerate(allowlist)]

    def unregistered(s: Subj):
        case, _ = resolve_expected_schema(eng, s.row.get("expected_schema_ref"))
        return Hit(case=case) if case is not None else None

    def violation(s: Subj):
        case, _ = resolve_expected_schema(eng, s.row.get("expected_schema_ref"))
        if case is not None:
            return None
        try:
            schema = load_schema_ref(schema_map, s.row["expected_schema_ref"], contract.member_law)
        except ExpressionError:
            return Hit(case="EXPECTED_SCHEMA_RESOLVED", pointer="")
        errors = _validation_errors(validator_for(schema, registered=True), eng.accepted[s.index]["parsed"])
        tokens = first_failure_tokens(errors) if errors else None
        return Hit(case="EXPECTED_SCHEMA_RESOLVED", pointer=pointer_of(tokens)) if tokens is not None else None

    scan(eng, "PE-38", subjects, {"BOUND_SCHEMA_MEMBER_UNREGISTERED": unregistered, "BOUND_SCHEMA_VIOLATION": violation})


# --- stage 21 group 4: reserved input declarations -------------------------------------------------------
_RESERVED_SOURCE_VALID = {
    "candidate_copy_authority": lambda v: v is False,
    "content_encoding": lambda v: v == "BASE64_RAW_FILE_BYTES",
    "decode": lambda v: v == "STRICT_BASE64_TO_RAW_UTF8_JSON",
    "use_after_pin_verification_only": lambda v: v is True,
}


def _token_array_valid(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(nonempty(token) for token in value)


@group_handler("PE-41")
def _pe41(eng: Engine) -> None:
    metacontract = eng.metacontract
    rows = metacontract.get("reserved_inputs")
    rows = rows if isinstance(rows, list) else []
    origins = metacontract.get("binding_origins") if isinstance(metacontract.get("binding_origins"), Mapping) else {}
    allowed = origins.get("allowed_origins") if isinstance(origins.get("allowed_origins"), list) else []
    expectations = origins.get("reserved_input_expectations")
    expectations = expectations if isinstance(expectations, Mapping) else {}
    by_name: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if isinstance(row, Mapping) and nonempty(row.get("name")) and row["name"] not in by_name:
            by_name[row["name"]] = row

    def base(i: int) -> str:
        return "/reserved_inputs/%d" % i

    def expectation_of(row: Mapping[str, Any]) -> Mapping[str, Any] | None:
        found = expectations.get(row.get("name")) if nonempty(row.get("name")) else None
        return found if isinstance(found, Mapping) else None

    def declaration_invalid(s: Subj):
        if not isinstance(s.row, Mapping):
            return Hit(pointer=base(s.index))
        for member in next(c for c in FAMILIES["PE-41"]["conditions"]
                           if c["condition_id"] == "RESERVED_INPUT_DECLARATION_INVALID")["checked_members"]:
            if not nonempty(s.row.get(member)):
                return Hit(pointer=base(s.index) + "/" + member)
        return None

    def not_unique(s: Subj):
        if not isinstance(s.row, Mapping) or not nonempty(s.row.get("name")):
            return None
        for earlier in range(s.index):
            other = rows[earlier]
            if isinstance(other, Mapping) and other.get("name") == s.row["name"]:
                return Hit(pointer=base(s.index) + "/name")
        return None

    def origin_undeclared(s: Subj):
        if isinstance(s.row, Mapping) and nonempty(s.row.get("origin")) and s.row["origin"] not in allowed:
            return Hit(pointer=base(s.index) + "/origin")
        return None

    def label_mismatch(s: Subj):
        expected = expectation_of(s.row) if isinstance(s.row, Mapping) else None
        if expected is None:
            return None
        for member in next(c for c in FAMILIES["PE-41"]["conditions"]
                           if c["condition_id"] == "RESERVED_INPUT_NAME_LABEL_MISMATCH")["checked_members"]:
            if s.row.get(member) != expected.get(member):
                return Hit(pointer=base(s.index) + "/" + member)
        return None

    def name_set_mismatch(_: Subj):
        declared = {row["name"] for row in rows if isinstance(row, Mapping) and nonempty(row.get("name"))}
        return Hit() if declared != set(expectations) else None

    def source_container(s: Subj):
        return s.row.get("profile_content_source", _ABSENT) if isinstance(s.row, Mapping) else _ABSENT

    def source_invalid(s: Subj):
        source = source_container(s)
        if source is _ABSENT:
            return None
        if not isinstance(source, Mapping):
            return Hit(pointer=base(s.index) + "/profile_content_source")
        for member in next(c for c in FAMILIES["PE-41"]["conditions"]
                           if c["condition_id"] == "RESERVED_CONTENT_SOURCE_INVALID")["checked_members"]:
            name = member.split("/", 1)[1]
            if name not in source or not _RESERVED_SOURCE_VALID[name](source[name]):
                return Hit(pointer=base(s.index) + "/" + member)
        return None

    def pointer_invalid(s: Subj):
        source = source_container(s)
        if not isinstance(source, Mapping):
            return None
        for member in next(c for c in FAMILIES["PE-41"]["conditions"]
                           if c["condition_id"] == "RESERVED_CONTENT_POINTER_INVALID")["checked_members"]:
            if not _token_array_valid(source.get(member.split("/", 1)[1])):
                return Hit(pointer=base(s.index) + "/" + member)
        return None

    def transport_invalid(s: Subj):
        source = source_container(s)
        if not isinstance(source, Mapping):
            return None
        transport = by_name.get(source.get("argument"))
        valid = (transport is not None and "profile_content_source" not in transport
                 and transport.get("origin") == "EXTERNAL_ACCEPTANCE_PROFILE")
        return None if valid else Hit(pointer=base(s.index) + "/profile_content_source/argument")

    def pin_undeclared(s: Subj):
        expected = expectation_of(s.row) if isinstance(s.row, Mapping) else None
        if expected is None or expected.get("pin_ref") is None:
            return None
        source = source_container(s)
        if not isinstance(source, Mapping):
            return Hit(pointer=base(s.index) + "/profile_content_source")
        if not json_equal(source.get("pin_pointer_tokens", _ABSENT), expected["pin_ref"]):
            return Hit(pointer=base(s.index) + "/profile_content_source/pin_pointer_tokens")
        return None

    subjects = [Subj("RESERVED_INPUT_ROW", index=index, row=row) for index, row in enumerate(rows)]
    subjects.append(Subj("RESERVED_INPUT_COLLECTION"))
    scan(eng, "PE-41", subjects, {
        "RESERVED_INPUT_DECLARATION_INVALID": declaration_invalid, "RESERVED_INPUT_DECLARATION_NOT_UNIQUE": not_unique,
        "RESERVED_INPUT_ORIGIN_UNDECLARED": origin_undeclared, "RESERVED_INPUT_NAME_LABEL_MISMATCH": label_mismatch,
        "RESERVED_INPUT_NAME_SET_MISMATCH": name_set_mismatch, "RESERVED_CONTENT_SOURCE_INVALID": source_invalid,
        "RESERVED_CONTENT_POINTER_INVALID": pointer_invalid, "RESERVED_CONTENT_SOURCE_TRANSPORT_INVALID": transport_invalid,
        "RESERVED_CONTENT_SOURCE_PIN_UNDECLARED": pin_undeclared})
    eng.reserved_declarations = OrderedDict((row["name"], dict(row)) for row in rows)


# --- stage 21 group 5: reserved input producer schema -------------------------------------------------------
@group_handler("PE-39")
def _pe39(eng: Engine) -> None:
    contract = eng.load_contract()
    schema_map = {key: obj for key, obj in eng.candidate_by_ref.items() if obj.registration.get("kind") == "SCHEMA"}
    rows = eng.metacontract["reserved_inputs"]
    subjects = [Subj("PRODUCER_SCHEMA_RESERVED_INPUT", index=index, row=row) for index, row in enumerate(rows)
                if isinstance(row.get("profile_content_source"), Mapping)
                and "producer_schema_ref" in row["profile_content_source"]]

    def unresolved(s: Subj):
        case, _ = resolve_expected_schema(eng, s.row["profile_content_source"]["producer_schema_ref"])
        return Hit() if case is not None else None

    def violation(s: Subj):
        tokens = s.row["profile_content_source"].get("pin_pointer_tokens")
        if not (isinstance(tokens, list) and len(tokens) == 2 and tokens[0] == "frozen_authority_pins"
                and tokens[1] in eng.frozen_content):
            return None
        ref = s.row["profile_content_source"]["producer_schema_ref"]
        try:
            schema = load_schema_ref(schema_map, ref, contract.member_law)
        except ExpressionError:
            return None
        errors = _validation_errors(validator_for(schema, registered=True), eng.frozen_content[tokens[1]][1])
        found = first_failure_tokens(errors) if errors else None
        return Hit(pointer=pointer_of(found)) if found is not None else None

    scan(eng, "PE-39", subjects, {"PRODUCER_SCHEMA_UNRESOLVED": unresolved, "PRODUCER_SCHEMA_VIOLATION": violation})


# --- stage 21 group 6: runtime representation ------------------------------------------------------------------
@group_handler("PE-40")
def _pe40(eng: Engine) -> None:
    value_schemas = ptr_lookup(eng.metacontract, "/runtime_representation/value_schemas")
    value_schemas = value_schemas if isinstance(value_schemas, Mapping) else {}
    names = sorted(value_schemas, key=utf16_key)

    def schema_invalid(s: Subj):
        schema = value_schemas[s.name]
        if metaschema_valid(schema):
            return None
        return Hit(tokens=metaschema_first_failure_tokens(schema) or [])

    def universe_invalid(_: Subj):
        errors = _validation_errors(validator_for(value_schemas["verification_universe"]), eng.universe_view)
        tokens = first_failure_tokens(errors) if errors else None
        # UNIVERSE_REPRESENTATION declares FIRST_INVALID_LOCATION_CANONICAL_PREORDER (the pointer of the first invalid
        # location); the tokens remain the location the identity derivation inspects.
        return Hit(tokens=tokens, pointer=pointer_of(tokens)) if tokens is not None else None

    def record_invalid(s: Subj):
        errors = _validation_errors(validator_for(value_schemas["resolved_object"]), eng.universe_view["objects"][s.k])
        tokens = first_failure_tokens(errors) if errors else None
        return Hit(tokens=tokens) if tokens is not None else None

    subjects = [Subj("RUNTIME_VALUE_SCHEMA", name=name) for name in names]
    subjects.append(Subj("UNIVERSE_VALUE"))
    subjects.extend(Subj("UNIVERSE_OBJECT_RECORD", k=k) for k in range(len(eng.universe_view["objects"])))
    scan(eng, "PE-40", subjects, {"VALUE_SCHEMA_INVALID": schema_invalid, "UNIVERSE_REPRESENTATION": universe_invalid,
                                  "RESOLVED_OBJECT_REPRESENTATION": record_invalid})



# ---------------------------------------------------------------------------
# Stage 22: static validation of the procedure registry, witness identities, bindings and the projection.
# ---------------------------------------------------------------------------
class StaticDocs:
    """The package-referenced registries and the metacontract sections that stage 22 is defined over."""

    def __init__(self, eng: Engine):
        package = eng.package

        def content(member: str) -> Any:
            obj = eng.candidate_by_ref.get(identity(package.get(member) or {}))
            return obj.content if obj is not None else {}
        self.eng = eng
        self.typers: dict[str, "SchemaTyper"] = {}
        self.metacontract = eng.metacontract
        self.primitive_registry = content("primitive_registry_ref")
        self.procedure_registry = content("procedure_registry_ref")
        self.invariant_registry = content("invariant_registry_ref")
        self.rule_registry = content("rule_registry_ref")

        def listed(document: Any, key: str) -> list[Any]:
            value = document.get(key) if isinstance(document, Mapping) else None
            return value if isinstance(value, list) else []
        self.primitives = listed(self.primitive_registry, "primitives")
        self.procedures = listed(self.procedure_registry, "procedures")
        self.invariants = listed(self.invariant_registry, "invariants")
        self.rules = listed(self.rule_registry, "rules")
        rep = self.metacontract.get("runtime_representation", {}) if isinstance(self.metacontract, Mapping) else {}
        calculus = rep.get("static_type_calculus", {}) if isinstance(rep, Mapping) else {}
        operator_rules = calculus.get("operator_rules", {}) if isinstance(calculus, Mapping) else {}
        self.operators: Mapping[str, Any] = operator_rules.get("operators", {}) if isinstance(operator_rules, Mapping) else {}
        self.slot_kinds: Mapping[str, str] = operator_rules.get("argument_type_slot_kinds", {}) if isinstance(operator_rules, Mapping) else {}
        self.static_paths: Mapping[str, Any] = rep.get("static_paths", {}) if isinstance(rep, Mapping) else {}
        self.limits: Mapping[str, Any] = self.metacontract.get("resource_limits", {}) if isinstance(self.metacontract, Mapping) else {}
        self.procedure_by_id = {p.get("procedure_id"): p for p in self.procedures if isinstance(p, Mapping)}
        self.invariant_by_id = {i.get("invariant_id"): i for i in self.invariants if isinstance(i, Mapping)}

    def measured_limit(self, measurement: Mapping[str, Any]) -> int:
        """The limit a measurement object references (limit_ref: metacontract:/resource_limits/<name>)."""
        reference = measurement["limit_ref"]
        prefix = "metacontract:"
        value = ptr_lookup(self.metacontract, reference[len(prefix):]) if reference.startswith(prefix) else _ABSENT
        if isinstance(value, bool) or not isinstance(value, int):
            raise ModelGap("RESOURCE_LIMIT_UNAVAILABLE:" + str(reference))
        return value

    def schema_instance_type(self, reference: Mapping[str, Any]) -> str | None:
        """SCHEMA_INSTANCE<S> for a RULE_BINDING argument whose expected_schema_ref S resolves to a registered SCHEMA
        document (and optional registered member); None when S is not resolvable (the declared argument type applies)."""
        type_name = "SCHEMA_INSTANCE<%s@%s%s>" % (reference.get("id"), reference.get("version"),
                                                  "#" + str(reference["member_id"]) if "member_id" in reference else "")
        if type_name not in self.typers:
            try:
                schema_map = {key: obj for key, obj in self.eng.candidate_by_ref.items() if obj.registration.get("kind") == "SCHEMA"}
                self.typers[type_name] = SchemaTyper(load_schema_ref(schema_map, reference, self.eng.load_contract().member_law))
            except Exception:
                return None
        return type_name

    def bootstrap_content(self, argument: str) -> Any:
        """Content of the declared bootstrap object named by its argument (the candidate package or a package-referenced one)."""
        member = BOOTSTRAP_OBJECTS[argument]["package_member"]
        if member is None:
            return self.eng.package
        obj = self.eng.candidate_by_ref.get(identity(self.eng.package.get(member) or {}))
        return obj.content if obj is not None else None

    def limit(self, name: str) -> int:
        return int(self.limits[name])

    def slots_of(self, node: Any) -> list[list[str]] | None:
        if not isinstance(node, Mapping) or not isinstance(node.get("op"), str):
            return None
        spec = self.operators.get(node["op"])
        return spec["slots"] if isinstance(spec, Mapping) else None


def _set_exact_pointer(items: Sequence[Any], expected: set[str], key: str, collection: str) -> Hit | None:
    ids = [item.get(key) if isinstance(item, Mapping) else None for item in items]
    extra = set_extra_index(ids, expected)
    if extra is not None:
        return Hit(pointer="%s/%d" % (collection, extra))
    return Hit(pointer=collection) if set(ids) != expected else None


def descendant_vector_failure(registry: Any) -> str | None:
    """Pointer of the first descendant conformance vector that is not reproduced (None when all are)."""
    if not isinstance(registry, Mapping):
        return "/descendant_conformance_vectors"
    vectors = registry.get("descendant_conformance_vectors")
    definition = registry.get("descendant_record")
    if not isinstance(vectors, list) or not vectors or not isinstance(definition, Mapping):
        return "/descendant_conformance_vectors"
    emitted = list(descendants({})[0].keys())
    shape = definition.get("record_shape") if isinstance(definition.get("record_shape"), Mapping) else {}
    fields = definition.get("fields") if isinstance(definition.get("fields"), Mapping) else {}
    if list(shape.get("field_order", [])) != emitted or shape.get("field_count") != len(emitted) or sorted(fields) != sorted(emitted):
        return "/descendant_conformance_vectors"
    for index, vector in enumerate(vectors):
        pointer = "/descendant_conformance_vectors/%d" % index
        if not isinstance(vector, Mapping):
            return pointer
        try:
            actual = descendants(vector.get("input"))
        except ExpressionError:
            return pointer
        if len(actual) != vector.get("expected_record_count") or actual != vector.get("expected_records"):
            return pointer
        for row in actual:
            chain = row["ancestor_pointers"]
            if not chain or chain[0] != "" or chain[-1] != row["pointer"]:
                return pointer
        probe = vector.get("ancestry_semantics_probe")
        if isinstance(probe, Mapping):
            observed = next((row["ancestor_pointers"] for row in actual if row["pointer"] == probe.get("probe_pointer")), None)
            if (probe.get("selected_semantics") != "INCLUSIVE_ROOT_THROUGH_SELF"
                    or observed != probe.get("inclusive_expected_ancestor_pointers")
                    or observed == probe.get("strict_expected_ancestor_pointers")):
                return pointer
        exclusion = vector.get("exclusion_probe")
        if isinstance(exclusion, Mapping):
            excluded = exclusion.get("excluded_pointer")
            if ([row["pointer"] for row in actual if excluded in row["ancestor_pointers"]] != exclusion.get("expected_excluded_node_pointers")
                    or [row["pointer"] for row in actual if excluded not in row["ancestor_pointers"]]
                    != exclusion.get("expected_included_node_pointers")):
                return pointer
    return None


def _referenced_ids(eng: Engine, docs: StaticDocs, reference: Any) -> list[Any] | None:
    """LABEL_COLON_POINTER_RESOLVED_IN_THE_NAMED_BOOTSTRAP_OBJECT: '<label>:<pointer>' (e.g.
    rule-registry:/provenance/required_rule_ids) names a declared bootstrap object by its label (the bootstrap
    argument with '-' for '_') and an RFC6901 pointer inside that object; the complete referenced array is returned."""
    if not isinstance(reference, str) or ":" not in reference:
        return None
    label, pointer = reference.split(":", 1)
    argument = label.replace("-", "_")
    if argument not in BOOTSTRAP_OBJECTS:
        return None
    document = docs.bootstrap_content(argument)
    value = ptr_lookup(document, pointer) if document is not None else _ABSENT
    return value if isinstance(value, list) else None


@group_handler("PE-45")
def _pe45(eng: Engine) -> None:
    docs = StaticDocs(eng)
    package = eng.package
    conditions = {c["condition_id"]: c for c in FAMILIES["PE-45"]["conditions"]}

    def primitive_set(_: Subj):
        return _set_exact_pointer(docs.primitives, set(docs.operators), "primitive_id",
                                  conditions["PRIMITIVE_SET_EXACT_TO_STATIC_TYPE_CALCULUS"]["location_template"])

    def primitive_signature(_: Subj):
        for index, primitive in enumerate(docs.primitives):
            spec = docs.operators.get(primitive.get("primitive_id")) if isinstance(primitive, Mapping) else None
            if spec is None:
                continue
            arguments = primitive.get("arguments")
            slots = spec["slots"]
            valid = (isinstance(arguments, list) and len(arguments) == len(slots)
                     and all(isinstance(a, Mapping) and a.get("name") == slot[0] and a.get("type") in docs.slot_kinds
                             and docs.slot_kinds[a["type"]] == slot[1] for a, slot in zip(arguments, slots))
                     and primitive.get("output_type") == spec["result"])
            if not valid:
                return Hit(pointer="/primitives/%d" % index)
        return None

    def descendant_vectors(_: Subj):
        set_descendant_limits(docs.limits)
        pointer = descendant_vector_failure(docs.primitive_registry)
        return Hit(pointer=pointer) if pointer is not None else None

    def procedure_set(_: Subj):
        expected = {i.get("procedure_id") for i in docs.invariants if isinstance(i, Mapping)}
        return _set_exact_pointer(docs.procedures, expected, "procedure_id", "/procedures")

    def invariant_set(_: Subj):
        required = package.get("required_invariant_ids")
        return _set_exact_pointer(docs.invariants, set(required) if isinstance(required, list) else set(),
                                  "invariant_id", "/invariants")

    def rule_set(_: Subj):
        # compared_sets: every /rules item of the bound rule registry (whatever its declared_class) against the
        # complete array referenced by the candidate package's required_rule_ids_ref.
        compared = conditions["BOUND_RULE_SET_EXACT_TO_REQUIRED_RULE_IDS"]["compared_sets"]
        bound_set, required_set = compared["bound"], compared["required"]
        if (compared["relation"] != "BOUND_IDS_UNIQUE_AND_SET_EQUAL_TO_REQUIRED_IDS"
                or compared["executable_subset_is_the_compared_set"] is not False
                or bound_set["scope"] != "EVERY_RULE_WHATEVER_ITS_DECLARED_CLASS"
                or required_set["scope"] != "THE_COMPLETE_REFERENCED_ARRAY"
                or required_set["resolution"] != "LABEL_COLON_POINTER_RESOLVED_IN_THE_NAMED_BOOTSTRAP_OBJECT"
                or bound_set["object"] not in BOOTSTRAP_OBJECTS or required_set["object"] not in BOOTSTRAP_OBJECTS):
            raise ModelGap("COMPARED_SETS_UNSUPPORTED")
        collection = ptr_lookup(docs.bootstrap_content(bound_set["object"]), bound_set["collection_pointer"])
        items = collection if isinstance(collection, list) else []
        reference = ptr_lookup(docs.bootstrap_content(required_set["object"]), required_set["reference_member"])
        required = _referenced_ids(eng, docs, reference if reference is not _ABSENT else None)
        return _set_exact_pointer(items, set(required) if required is not None else set(), bound_set["member"],
                                  bound_set["collection_pointer"])

    def procedure_bindings(_: Subj):
        bindings = docs.metacontract.get("procedure_bindings")
        bindings = bindings if isinstance(bindings, list) else []
        seen: set[Any] = set()
        for index, binding in enumerate(bindings):
            inv_id = binding.get("invariant_id") if isinstance(binding, Mapping) else None
            invariant = docs.invariant_by_id.get(inv_id)
            if (invariant is None or inv_id in seen or binding.get("procedure_id") != invariant.get("procedure_id")):
                return Hit(pointer="/procedure_bindings/%d" % index)
            seen.add(inv_id)
        return Hit(pointer="/procedure_bindings") if seen != set(docs.invariant_by_id) else None

    def rule_invariant_binding(_: Subj):
        for index, rule in enumerate(docs.rules):
            binding = rule.get("invariant_binding") if isinstance(rule, Mapping) else None
            if not isinstance(binding, Mapping):
                continue
            invariant = docs.invariant_by_id.get(binding.get("invariant_id"))
            procedure = docs.procedure_by_id.get(invariant.get("procedure_id")) if invariant is not None else None
            declared = ({a.get("name") for a in procedure.get("arguments", []) if isinstance(a, Mapping)
                         and a.get("origin") == "RULE_BINDING"} if procedure is not None else None)
            arguments = binding.get("arguments", {})
            if declared is None or not isinstance(arguments, Mapping) or set(arguments) - declared:
                return Hit(pointer="/rules/%d/invariant_binding" % index)
        return None

    def reserved_bindings(_: Subj):
        declarations = {row.get("name"): row for row in docs.metacontract.get("reserved_inputs", []) if isinstance(row, Mapping)}
        bindings = docs.metacontract.get("procedure_bindings")
        for index, binding in enumerate(bindings if isinstance(bindings, list) else []):
            if not isinstance(binding, Mapping):
                continue
            procedure = docs.procedure_by_id.get(binding.get("procedure_id"))
            arguments = {a.get("name"): a for a in procedure.get("arguments", []) if isinstance(a, Mapping)} if procedure else {}
            reserved = binding.get("reserved_bindings", [])
            for position, row in enumerate(reserved if isinstance(reserved, list) else []):
                declared = declarations.get(row.get("name")) if isinstance(row, Mapping) else None
                argument = arguments.get(row.get("name")) if isinstance(row, Mapping) else None
                if (declared is None or argument is None or row.get("type") != declared.get("type")
                        or row.get("origin") != declared.get("origin") or argument.get("type") != row.get("type")
                        or argument.get("origin") != row.get("origin")):
                    return Hit(pointer="/procedure_bindings/%d/reserved_bindings/%d" % (index, position))
        return None

    def source_constraints(_: Subj):
        schema_obj = eng.candidate_by_ref.get(identity(ptr_lookup(docs.procedure_registry, "/schema_ref") or {}))
        grammar = ptr_lookup(schema_obj.content, "/$defs/source_constraint") if schema_obj is not None else _ABSENT
        for index, procedure in enumerate(docs.procedures):
            for position, argument in enumerate(procedure.get("arguments", []) if isinstance(procedure, Mapping) else []):
                if not isinstance(argument, Mapping) or argument.get("origin") != "RULE_BINDING":
                    continue
                pointer = "/procedures/%d/arguments/%d/source_constraint" % (index, position)
                if "source_constraint" not in argument:
                    return Hit(pointer=pointer)
                if grammar is not _ABSENT and _validation_errors(validator_for(grammar, schema_obj.content),
                                                                  argument["source_constraint"]):
                    return Hit(pointer=pointer)
        return None

    def result_type(_: Subj):
        for index, procedure in enumerate(docs.procedures):
            result = procedure.get("result") if isinstance(procedure, Mapping) else None
            if not (isinstance(result, Mapping) and result.get("type") in ("BOOLEAN", "TRUST_RESULT")):
                return Hit(pointer="/procedures/%d/result/type" % index)
        return None

    def trust_owner(_: Subj):
        owner = ptr_lookup(docs.metacontract, "/result_contracts/trust_result/owner_procedure_id")
        trusted = [(index, p.get("procedure_id")) for index, p in enumerate(docs.procedures)
                   if isinstance(p, Mapping) and isinstance(p.get("result"), Mapping) and p["result"].get("type") == "TRUST_RESULT"]
        seen: set[Any] = set()
        for index, procedure_id in trusted:
            if procedure_id != owner or procedure_id in seen:
                return Hit(pointer="/procedures/%d" % index)
            seen.add(procedure_id)
        return Hit(pointer="/procedures") if seen != {owner} else None

    def assertion_codes(every_invariant: bool):
        def test(_: Subj):
            for index, procedure in enumerate(docs.procedures):
                if not isinstance(procedure, Mapping):
                    continue
                compatible = procedure.get("compatible_failure_codes")
                allowed = [i.get("compatible_failure_codes") for i in docs.invariants if isinstance(i, Mapping)
                           and i.get("procedure_id") == procedure.get("procedure_id")] if every_invariant else [compatible]
                for position, assertion in enumerate(procedure.get("assertions", [])):
                    code = assertion.get("failure_code") if isinstance(assertion, Mapping) else None
                    if any(not isinstance(codes, list) or code not in codes for codes in allowed):
                        return Hit(pointer="/procedures/%d/assertions/%d/failure_code" % (index, position))
            return None
        return test

    scan(eng, "PE-45", [Subj("STATIC_DECLARATION_SITE")], {
        "PRIMITIVE_SET_EXACT_TO_STATIC_TYPE_CALCULUS": primitive_set,
        "PRIMITIVE_SIGNATURE_MATCHES_STATIC_TYPE_CALCULUS": primitive_signature,
        "DESCENDANT_CONFORMANCE_VECTORS_REPRODUCED": descendant_vectors,
        "PROCEDURE_ID_SET_EXACT": procedure_set,
        "INVARIANT_SET_EXACT_TO_PACKAGE_REQUIRED_INVARIANT_IDS": invariant_set,
        "BOUND_RULE_SET_EXACT_TO_REQUIRED_RULE_IDS": rule_set,
        "INVARIANT_PROCEDURE_BINDINGS_EXACT": procedure_bindings,
        "RULE_INVARIANT_BINDING_RESOLVES": rule_invariant_binding,
        "RESERVED_BINDINGS_IMMUTABLE": reserved_bindings,
        "RULE_BINDING_SOURCE_CONSTRAINTS_VALID": source_constraints,
        "PROCEDURE_RESULT_TYPE_DECLARED": result_type,
        "TRUST_RESULT_OWNER_EXACT": trust_owner,
        "ASSERTION_CODES_IN_PROCEDURE_COMPATIBLE_SET": assertion_codes(False),
        "ASSERTION_CODES_IN_EVERY_BOUND_INVARIANT_SET": assertion_codes(True),
    })
    eng.static_docs = docs  # type: ignore[attr-defined]


# --- PE-44: procedure AST ------------------------------------------------------------------------------
from urllib.parse import unquote


class AstFail(Exception):
    def __init__(self, condition: str, tokens: Sequence[Any]):
        super().__init__(condition)
        self.condition = condition
        self.tokens = list(tokens)


# The AST resource-limit law (model:/protocol_constants/ast_resource_limits) and the measurement objects of the PE-44
# conditions are consumed declaratively: AST roots, node forms, child edges by slot kind, the collection binder
# inventory, the measurement functions, the comparison and the limit references are all read from the committed model.
AST_LAW = PC["ast_resource_limits"]
PE44_MEASUREMENTS: dict[str, Mapping[str, Any]] = {
    row["condition_id"]: row["measurement"] for row in FAMILIES["PE-44"]["conditions"] if "measurement" in row}
_PE44_PROCEDURE_MEASUREMENTS = ("MAX_ARGUMENTS_PER_PROCEDURE_EXCEEDED", "MAX_ASSERTIONS_PER_PROCEDURE_EXCEEDED",
                                "MAX_AST_NODES_PER_PROCEDURE_EXCEEDED")
_CHILD_EDGE_RULES = ("NO_CHILD_EDGE", "THE_VALUE_PRESENT_AT_THE_SLOT",
                     "THE_VALUE_PRESENT_AT_THE_SLOT_WHEN_IT_IS_A_JSON_OBJECT",
                     "EACH_MEMBER_VALUE_OF_THE_JSON_OBJECT_PRESENT_AT_THE_SLOT")
AMBIGUOUS_JSON = "JSON<BRANCH_AMBIGUOUS>"
# Operand domains that accept every JSON value: a branch-ambiguous JSON result is never a narrow consumer's input there.
_WIDE_OPERAND_TYPES = {"JSON", "FINITE_JSON", "JSON_OR_RESOLVED_OBJECT", "JSON_EXPRESSION", "MODE_EXPRESSION"}


def ast_law_conformance() -> None:
    """Startup proof that this evaluator implements every token the declared AST resource-limit law uses."""
    def expect(condition: bool, label: str) -> None:
        if not condition:
            raise ModelGap("AST_RESOURCE_LIMIT_LAW_UNSUPPORTED:" + label)
    ast = AST_LAW["ast"]
    edges = ast["child_edges"]
    expect(set(edges["by_slot_kind"].values()) <= set(_CHILD_EDGE_RULES) <= set(CLOSED["ast_child_edge_rule"]), "child_edge_rules")
    expect(edges["absent_slot"] == "NO_CHILD_EDGE" and edges["undeclared_member"] == "NO_CHILD_EDGE", "absent_or_undeclared_edge")
    expect(edges["child_order"] == {"named_expression_map_members": "UTF16_CODE_UNIT_KEY_ORDER",
                                    "slots": "DECLARED_OPERATOR_SLOT_ORDER"}, "child_order")
    expect(ast["terminals"]["measured"] is True and ast["terminals"]["literal_payload_is_ast"] is False, "terminals")
    expect(AST_LAW["traversal"]["order"] == "CANONICAL_POSTORDER"
           and AST_LAW["traversal"]["first_failure"] == "FIRST_INVALID_SUBJECT_IN_TRAVERSAL_ORDER"
           and AST_LAW["traversal"]["procedure_level_subjects"] == "BEFORE_THE_NODES_OF_THE_SAME_PROCEDURE", "traversal")
    expect(FAMILIES["PE-44"]["subject_order"] == "AST_PROCEDURE_ASSERTION_POSTORDER"
           and MODEL["subject_order_rules"]["AST_PROCEDURE_ASSERTION_POSTORDER"] == "AST_PROCEDURE_ASSERTION_CANONICAL_POSTORDER"
           and AST_LAW["traversal"]["subject_order"] == "model:/subject_orders/AST_PROCEDURE_ASSERTION_POSTORDER"
           and "AST_PROCEDURE_ASSERTION_CANONICAL_POSTORDER" in CLOSED["ordering_rule"], "subject_order")
    expect(AST_LAW["ast"]["roots"]["root_order"] == "ASSERTIONS_IN_SOURCE_ORDER;CONDITION_ROOT_BEFORE_WITNESS_ROOT"
           and AST_LAW["ast"]["roots"]["rule"] == "EACH_ASSERTION_CONDITION_AND_EACH_ASSERTION_WITNESS_IS_A_SEPARATE_AST_ROOT", "roots")
    binders = AST_LAW["collection_binders"]
    expect(binders["complete"] is True and all(
        isinstance(spec.get("binder_slot"), str) and isinstance(spec.get("bound_slots"), list)
        and isinstance(spec.get("unbound_slots"), list) for spec in binders["operators"].values()), "collection_binders")
    expect(set(PE44_MEASUREMENTS) == set(_PE44_PROCEDURE_MEASUREMENTS) | {"MAX_EXPRESSION_DEPTH_EXCEEDED",
                                                                          "MAX_LEXICAL_COLLECTION_NESTING_EXCEEDED"}, "measurements")
    for condition_id, measurement in PE44_MEASUREMENTS.items():
        expect(measurement["comparison"] in CLOSED["limit_comparison"] and measurement["limit_inclusive"] is True
               and measurement["function"] in CLOSED["resource_limit_function"]
               and str(measurement["limit_ref"]).startswith("metacontract:/resource_limits/"), condition_id + ":comparison")
    for condition_id in _PE44_PROCEDURE_MEASUREMENTS:
        measurement = PE44_MEASUREMENTS[condition_id]
        expect(measurement["subject"] == "PROCEDURE_DECLARATION"
               and measurement["location"] == "LOCATION_TEMPLATE_WITH_THE_PROCEDURE_INDEX"
               and measurement["first_failure"] == "PROCEDURE_LEVEL_SUBJECT_IN_PROCEDURE_SOURCE_ORDER", condition_id + ":subject")
    for condition_id in _PE44_PROCEDURE_MEASUREMENTS[:2]:
        expect(PE44_MEASUREMENTS[condition_id]["function"] == "ARRAY_LENGTH"
               and isinstance(PE44_MEASUREMENTS[condition_id]["measured_member"], str), condition_id + ":function")
    nodes = PE44_MEASUREMENTS["MAX_AST_NODES_PER_PROCEDURE_EXCEEDED"]
    expect(nodes["function"] == "AST_NODE_COUNT" and nodes["terminals_counted"] is True
           and nodes["literal_payload_counted"] is False, "MAX_AST_NODES:function")
    depth = PE44_MEASUREMENTS["MAX_EXPRESSION_DEPTH_EXCEEDED"]
    expect(depth["function"] == "NODE_DEPTH" and depth["subject"] == "AST_NODE" and depth["terminals_measured"] is True
           and depth["location"] == "POINTER_OF_THE_FAILING_NODE" and depth["first_failure"] == "FIRST_INVALID_NODE_IN_CANONICAL_POSTORDER"
           and isinstance(depth["root_value"], int) and isinstance(depth["edge_increment"], int), "MAX_EXPRESSION_DEPTH:function")
    nesting = PE44_MEASUREMENTS["MAX_LEXICAL_COLLECTION_NESTING_EXCEEDED"]
    expect(nesting["function"] == "ACTIVE_COLLECTION_BINDER_COUNT" and nesting["subject"] == "AST_NODE"
           and nesting["terminals_measured"] is True and nesting["location"] == "POINTER_OF_THE_FAILING_NODE"
           and nesting["first_failure"] == "FIRST_INVALID_NODE_IN_CANONICAL_POSTORDER"
           and nesting["binder_node_value"] == "CURRENT_COUNT" and nesting["unbound_slot_value"] == "CURRENT_COUNT"
           and nesting["binder_set_ref"] == "model:/protocol_constants/ast_resource_limits/collection_binders/operators"
           and isinstance(nesting["root_value"], int) and isinstance(nesting["entry_increment"], int)
           and isinstance(nesting["exit_decrement"], int), "MAX_LEXICAL_COLLECTION_NESTING:function")


def within_limit(measurement: Mapping[str, Any], value: int, limit: int) -> bool:
    """The declared inclusive comparison of a measurement: is `value` valid against `limit`?"""
    comparison = measurement["comparison"]
    if comparison == "VALUE_LESS_THAN_OR_EQUAL_TO_LIMIT":
        return value <= limit
    if comparison == "LOWER_BOUND_AND_VALUE_LESS_THAN_OR_EQUAL_TO_LIMIT":
        return measurement["lower_bound"] <= value <= limit
    raise ModelGap("LIMIT_COMPARISON_UNSUPPORTED:" + str(comparison))


def _assignable(expected: str, actual: str) -> bool:
    """Operand assignability over the declared static types (static_type_calculus.assignability)."""
    if actual == AMBIGUOUS_JSON:
        actual = "JSON"
    if actual == "JSON":
        return expected not in {"VERIFICATION_UNIVERSE", "RESOLVED_OBJECT", "SCOPE_NAME", "RFC6901_POINTER", "COMPARATOR"}
    if expected == "FINITE_JSON":
        return actual not in {"RESOLVED_OBJECT", "VERIFICATION_UNIVERSE"}
    if expected in {"JSON", "JSON_OR_RESOLVED_OBJECT", "JSON_EXPRESSION", "MODE_EXPRESSION"}:
        return True
    if expected == "JSON_OBJECT":
        return actual in {"JSON_OBJECT", "RESOLVED_OBJECT", "TYPED_REFERENCE", "BASE_TYPED_REFERENCE", "INTEGRITY"}
    if expected == "JSON_NUMBER":
        return actual in {"JSON_NUMBER", "NONNEGATIVE_INTEGER"}
    if expected == "RFC3339_STRING":
        return actual in {"STRING", "RFC3339_STRING"}
    if expected == "JSON_SCHEMA":
        return actual in {"JSON_SCHEMA", "JSON_OBJECT"}
    if expected in {"ARRAY<T>", "ARRAY<JSON>"}:
        return actual.startswith("ARRAY<") and actual.endswith(">")
    if expected == "BOOLEAN_EXPRESSION":
        return actual == "BOOLEAN"
    return expected == actual


_DESCENDABLE = {"JSON", "INTEGRITY", "TYPED_REFERENCE", "BASE_TYPED_REFERENCE", "TYPED_REFERENCE_OR_NULL",
                "ARRAY<STRING>", "ARRAY<RESOLVED_OBJECT>"}


class StaticTypeError(Exception):
    """A static error of the declared path calculus (known scalar with a pointer remainder, a non-index array token,
    or an undeclared field of a closed record)."""


class _TooComplex(Exception):
    """The effective schema has too many branch combinations to be analysed: no refinement is claimed."""


_SCHEMA_SCALAR_KINDS = {"string", "number", "boolean", "null"}
_SCHEMA_KIND_TYPE = {"object": "JSON_OBJECT", "string": "STRING", "number": "JSON_NUMBER", "boolean": "BOOLEAN", "null": "NULL"}


def _schema_value_kind(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if value is None:
        return "null"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float, Decimal)):
        return "number"
    return "array" if isinstance(value, list) else "object"


class SchemaTyper:
    """static_type_calculus.static_type_at_path for SCHEMA_INSTANCE<S>: the declared schema document bound to S is
    followed from its root by the declared keywords (properties, items, $ref, type, const, enum, allOf, oneOf, anyOf,
    additionalProperties; if/then/else and not add no refinement). The result is one determinate static type, plain
    JSON (no unique projection) or the branch-ambiguous JSON marker; a known static error raises StaticTypeError."""

    ALTERNATIVE_LIMIT = 512
    DEPTH_LIMIT = 48

    def __init__(self, root: Any):
        self.root = root
        self._cache: dict[tuple[str, ...], str] = {}

    # -- effective schema as alternatives of conjunctions of plain keyword objects ------------------------------
    def _resolve(self, reference: Any) -> Any:
        if not isinstance(reference, str) or not reference.startswith("#"):
            return _ABSENT
        return ptr_lookup(self.root, unquote(reference[1:]))

    def _cross(self, left: list[list[dict]], right: list[list[dict]]) -> list[list[dict]]:
        out = [a + b for a in left for b in right]
        if len(out) > self.ALTERNATIVE_LIMIT:
            raise _TooComplex()
        return out

    def _alternatives(self, schema: Any, depth: int = 0, active: frozenset = frozenset()) -> list[list[dict]]:
        if schema is False:
            return []
        if not isinstance(schema, Mapping) or depth > self.DEPTH_LIMIT:
            return [[{}]]
        alternatives: list[list[dict]] = [[{key: value for key, value in schema.items()
                                            if key not in ("allOf", "anyOf", "oneOf", "$ref")}]]
        reference = schema.get("$ref")
        if isinstance(reference, str) and reference not in active:
            target = self._resolve(reference)
            if target is not _ABSENT:
                alternatives = self._cross(alternatives, self._alternatives(target, depth + 1, active | {reference}))
        members = schema.get("allOf")
        if isinstance(members, list):
            for member in members:
                alternatives = self._cross(alternatives, self._alternatives(member, depth + 1, active))
        for keyword in ("oneOf", "anyOf"):
            branches = schema.get(keyword)
            if isinstance(branches, list) and branches:
                joined: list[list[dict]] = []
                for branch in branches:
                    joined.extend(self._alternatives(branch, depth + 1, active))
                alternatives = self._cross(alternatives, joined)
        return alternatives

    def _conjunction(self, schemas: Sequence[Any], depth: int) -> list[list[dict]]:
        alternatives: list[list[dict]] = [[{}]]
        for schema in schemas:
            alternatives = self._cross(alternatives, self._alternatives(schema, depth + 1))
        return alternatives

    # -- base kinds ---------------------------------------------------------------------------------------------
    @staticmethod
    def _plain_kinds(plain: Mapping[str, Any]) -> set[str] | None:
        constraints: list[set[str]] = []
        declared = plain.get("type")
        if isinstance(declared, str):
            constraints.append({"number" if declared == "integer" else declared})
        elif isinstance(declared, list) and declared and all(isinstance(item, str) for item in declared):
            constraints.append({"number" if item == "integer" else item for item in declared})
        if "const" in plain:
            constraints.append({_schema_value_kind(plain["const"])})
        enumerated = plain.get("enum")
        if isinstance(enumerated, list) and enumerated:
            constraints.append({_schema_value_kind(item) for item in enumerated})
        if not constraints:
            return None
        kinds = constraints[0]
        for other in constraints[1:]:
            kinds = kinds & other
        return kinds

    def _alternative_kinds(self, alternative: Sequence[Mapping[str, Any]]) -> set[str] | None:
        kinds: set[str] | None = None
        for plain in alternative:
            found = self._plain_kinds(plain)
            if found is not None:
                kinds = found if kinds is None else kinds & found
        return kinds

    # -- descent by one pointer token ---------------------------------------------------------------------------
    def _mentions(self, schema: Any, token: str, depth: int = 0) -> bool:
        if not isinstance(schema, Mapping) or depth > 16:
            return False
        properties = schema.get("properties")
        if isinstance(properties, Mapping) and token in properties:
            return True
        if any(self._mentions(schema.get(key), token, depth + 1) for key in ("if", "then", "else")):
            return True
        for key in ("allOf", "anyOf", "oneOf"):
            members = schema.get(key)
            if isinstance(members, list) and any(self._mentions(member, token, depth + 1) for member in members):
                return True
        return False

    def _members(self, alternative: Sequence[Mapping[str, Any]], token: str) -> list[Any]:
        declared: list[Any] = []
        for plain in alternative:
            properties = plain.get("properties")
            if isinstance(properties, Mapping) and token in properties:
                declared.append(properties[token])
            patterns = plain.get("patternProperties")
            if isinstance(patterns, Mapping):
                for pattern, schema in patterns.items():
                    try:
                        if re.search(pattern, token):
                            declared.append(schema)
                    except re.error:
                        continue
        if declared:
            return declared
        valued = [plain["additionalProperties"] for plain in alternative if isinstance(plain.get("additionalProperties"), Mapping)]
        if valued:
            return valued
        closed = any(plain.get("additionalProperties") is False for plain in alternative)
        if closed and not any(self._mentions(plain.get(key), token) for plain in alternative for key in ("if", "then", "else")):
            raise StaticTypeError("CLOSED_RECORD_UNDECLARED_FIELD")
        return []

    @staticmethod
    def _items(alternative: Sequence[Mapping[str, Any]], index: int) -> list[Any]:
        found: list[Any] = []
        for plain in alternative:
            prefix = plain.get("prefixItems")
            if isinstance(prefix, list) and index < len(prefix):
                found.append(prefix[index])
            elif isinstance(plain.get("items"), (Mapping, bool)):
                found.append(plain["items"])
        return found

    def _descend(self, alternative: Sequence[Mapping[str, Any]], kinds: set[str] | None, token: str) -> list[Any]:
        is_index = token.isascii() and token.isdigit() and (len(token) == 1 or token[0] != "0")
        if kinds is not None and kinds == {"array"}:
            if not is_index:
                raise StaticTypeError("NON_INDEX_TOKEN_ON_ARRAY")
            return self._items(alternative, int(token))
        if kinds is not None and kinds and kinds <= _SCHEMA_SCALAR_KINDS:
            raise StaticTypeError("KNOWN_SCALAR_WITH_POINTER_REMAINDER")
        if kinds is not None and kinds == {"object"}:
            return self._members(alternative, token)
        if is_index and any(isinstance(plain.get("items"), (Mapping, bool)) or isinstance(plain.get("prefixItems"), list)
                            for plain in alternative):
            return self._items(alternative, int(token))
        found = [schema for plain in alternative for schema in (
            [plain["properties"][token]] if isinstance(plain.get("properties"), Mapping) and token in plain["properties"] else [])]
        return found

    # -- typing -------------------------------------------------------------------------------------------------
    def _leaf(self, alternative: Sequence[Mapping[str, Any]], kinds: set[str] | None, depth: int) -> str:
        if kinds is None or len(kinds) != 1:
            return "JSON"
        kind = next(iter(kinds))
        if kind != "array":
            return _SCHEMA_KIND_TYPE[kind]
        items = [plain["items"] for plain in alternative if isinstance(plain.get("items"), (Mapping, bool))]
        element = self._type(self._conjunction(items, depth), [], depth + 1) if items else "JSON"
        return "ARRAY<%s>" % ("JSON" if element == AMBIGUOUS_JSON else element)

    @staticmethod
    def _domain(type_name: str) -> str:
        return "ARRAY" if type_name.startswith("ARRAY<") else type_name

    def _join(self, results: Sequence[str]) -> str:
        if AMBIGUOUS_JSON in results:
            return AMBIGUOUS_JSON
        distinct = list(dict.fromkeys(results))
        if len(distinct) == 1:
            return distinct[0]
        if "JSON" in distinct:
            return "JSON"
        if len({self._domain(name) for name in distinct}) == 1:
            return "ARRAY<JSON>"
        return AMBIGUOUS_JSON

    def _type(self, alternatives: Sequence[Sequence[Mapping[str, Any]]], tokens: Sequence[str], depth: int) -> str:
        if depth > self.DEPTH_LIMIT:
            return "JSON"
        results: list[str] = []
        failure: StaticTypeError | None = None
        for alternative in alternatives:
            kinds = self._alternative_kinds(alternative)
            if kinds is not None and not kinds:
                continue
            try:
                if tokens:
                    children = self._conjunction(self._descend(alternative, kinds, tokens[0]), depth)
                    results.append(self._type(children, tokens[1:], depth + 1))
                else:
                    results.append(self._leaf(alternative, kinds, depth))
            except StaticTypeError as error:
                failure = failure or error
        if not results:
            if failure is not None:
                raise failure
            return "JSON"
        return self._join(results)

    def type_at(self, tokens: Sequence[str]) -> str:
        key = tuple(tokens)
        if key not in self._cache:
            try:
                self._cache[key] = self._type(self._alternatives(self.root), list(tokens), 0)
            except _TooComplex:
                self._cache[key] = "JSON"
        return self._cache[key]


class AstChecker:
    """Node-level conditions of PE-44 in canonical postorder with operand slots in declared slot order."""

    def __init__(self, docs: StaticDocs, procedure: Mapping[str, Any]):
        self.docs = docs
        self.arguments = {a.get("name"): a for a in procedure.get("arguments", []) if isinstance(a, Mapping)}
        self.argument_types = {}
        for name, spec in self.arguments.items():
            if spec.get("type") == "VERIFICATION_UNIVERSE":
                self.argument_types[name] = "VERIFICATION_UNIVERSE"
                continue
            # rule_binding_with_schema_ref: SCHEMA_INSTANCE<expected_schema_ref> (the bound schema document of the reference)
            expected_ref = (spec.get("source_constraint") or {}).get("expected_schema_ref") if spec.get("origin") == "RULE_BINDING" else None
            instance_type = docs.schema_instance_type(expected_ref) if isinstance(expected_ref, Mapping) else None
            self.argument_types[name] = instance_type or "JSON_OBJECT"
        self.primitives = {p.get("primitive_id"): p for p in docs.primitives if isinstance(p, Mapping)}
        self.depth_measure = PE44_MEASUREMENTS["MAX_EXPRESSION_DEPTH_EXCEEDED"]
        self.nesting_measure = PE44_MEASUREMENTS["MAX_LEXICAL_COLLECTION_NESTING_EXCEEDED"]
        self.max_depth = docs.measured_limit(self.depth_measure)
        self.max_nesting = docs.measured_limit(self.nesting_measure)
        self.binders: Mapping[str, Mapping[str, Any]] = AST_LAW["collection_binders"]["operators"]
        self.edge_rules: Mapping[str, str] = AST_LAW["ast"]["child_edges"]["by_slot_kind"]

    @staticmethod
    def expression_children(node: Mapping[str, Any], tokens: list[Any], slots: list[list[str]]):
        """(slot, slot_kind, child, child_tokens) in declared slot order (named maps by UTF-16 key order)."""
        for name, kind in slots:
            if kind == "EXPRESSION" and name in node:
                yield name, kind, node[name], tokens + [name]
            elif kind == "NAMED_EXPRESSION_MAP" and isinstance(node.get(name), Mapping):
                for key in sorted(node[name], key=utf16_key):
                    yield name, kind, node[name][key], tokens + [name, key]

    def declared_children(self, node: Any, tokens: list[Any], slots: Sequence[Sequence[str]] | None = None) -> list[tuple[str, str, Any, list[Any]]]:
        """Child edges of an AST node by the declared slot kind rule (ast_resource_limits.ast.child_edges): only a node
        whose op names a declared operator has children; slots in declared operator slot order, the members of a named
        expression map in UTF-16 code-unit key order."""
        operator_slots = self.docs.slots_of(node)
        if operator_slots is None:
            return []
        children: list[tuple[str, str, Any, list[Any]]] = []
        for name, kind in (operator_slots if slots is None else slots):
            rule = self.edge_rules.get(kind, "NO_CHILD_EDGE")
            if rule == "NO_CHILD_EDGE" or name not in node:
                continue
            value = node[name]
            if rule == "THE_VALUE_PRESENT_AT_THE_SLOT":
                children.append((name, kind, value, tokens + [name]))
            elif rule == "THE_VALUE_PRESENT_AT_THE_SLOT_WHEN_IT_IS_A_JSON_OBJECT":
                if isinstance(value, Mapping):
                    children.append((name, kind, value, tokens + [name]))
            elif rule == "EACH_MEMBER_VALUE_OF_THE_JSON_OBJECT_PRESENT_AT_THE_SLOT":
                if isinstance(value, Mapping):
                    for key in sorted(value, key=utf16_key):
                        children.append((name, kind, value[key], tokens + [name, key]))
            else:
                raise ModelGap("AST_CHILD_EDGE_RULE_UNSUPPORTED:" + str(rule))
        return children

    def node_count(self, root: Any) -> int:
        """AST_NODE_COUNT of one AST root: every node over the declared child edges (terminals and malformed values
        included, literal payloads never traversed)."""
        count = 0
        pending = [root]
        while pending:
            node = pending.pop()
            count += 1
            pending.extend(child for _, _, child, _ in self.declared_children(node, []))
        return count

    # -- measurement ---------------------------------------------------------------------------------------------
    def _beyond_limits(self, depth: int, nesting: int) -> bool:
        return (not within_limit(self.depth_measure, depth, self.max_depth)
                or not within_limit(self.nesting_measure, nesting, self.max_nesting))

    def _bound_context(self, node: Mapping[str, Any], slot_name: str, scopes: Mapping[str, str], nesting: int,
                       member_type: str = "JSON") -> tuple[Mapping[str, str], int]:
        """Scope and nesting count in which the child of `slot_name` is evaluated: the bound slots of a collection binder
        enter with the count increased by entry_increment, every other slot keeps the current count."""
        spec = self.binders.get(node.get("op")) if self.docs.slots_of(node) is not None else None
        if spec is None or slot_name not in spec["bound_slots"]:
            return scopes, nesting
        inner = dict(scopes)
        binder = node.get(spec["binder_slot"])
        if isinstance(binder, str):
            inner[binder] = member_type
        return inner, nesting + self.nesting_measure["entry_increment"]

    def visit(self, node: Any, tokens: list[Any], depth: int, scopes: Mapping[str, str], nesting: int) -> str:
        """Postorder visit of `node` (depth and nesting are the measured values at the node). A node beyond a measured
        limit makes every node of its subtree invalid for that measure, so the first invalid subject in canonical
        postorder is the first node of that subtree: it is reached directly along the first child edges."""
        if self._beyond_limits(depth, nesting):
            while True:
                children = self.declared_children(node, tokens)
                if not children:
                    break
                slot_name, _, child, child_tokens = children[0]
                scopes, nesting = self._bound_context(node, slot_name, scopes, nesting)
                node, tokens, depth = child, child_tokens, depth + self.depth_measure["edge_increment"]
        return self._visit_node(node, tokens, depth, scopes, nesting)

    def _eff(self, type_name: str) -> str:
        """SCHEMA_INSTANCE<S> is assignable to the declared base container or scalar of S."""
        typer = self.docs.typers.get(type_name)
        return typer.type_at([]) if typer is not None else type_name

    def _visit_node(self, node: Any, tokens: list[Any], depth: int, scopes: Mapping[str, str], nesting: int) -> str:
        docs = self.docs
        if not isinstance(node, Mapping):
            raise AstFail("EXACT_OPERATOR_OPERANDS", tokens)
        keys = set(node)
        slots = docs.slots_of(node)
        child_types: dict[str, str] = {}
        inner = dict(scopes)
        binder: str | None = None
        collection_type = "JSON"
        # children first (postorder), in declared operator slot order
        if slots is not None:
            spec = self.binders.get(node["op"])
            for slot_name, slot_kind in slots:
                if slot_kind == "SCOPE_BINDER":
                    value = node.get(slot_name)
                    binder = value if isinstance(value, str) else None
                    member_type = "RESOLVED_OBJECT" if collection_type == "ARRAY<RESOLVED_OBJECT>" else "JSON"
                    if binder is not None:
                        inner = dict(scopes)
                        inner[binder] = member_type
                    continue
                bound = spec is not None and slot_name in spec["bound_slots"]
                child_scopes = inner if bound else scopes
                child_nesting = nesting + self.nesting_measure["entry_increment"] if bound else nesting
                for slot, kind, child, child_tokens in self.declared_children(node, tokens, [[slot_name, slot_kind]]):
                    child_type = self.visit(child, child_tokens, depth + self.depth_measure["edge_increment"], child_scopes, child_nesting)
                    if slot_name not in child_types:
                        child_types[slot_name] = child_type
                    if kind == "EXPRESSION" and slot_name == slots[0][0]:
                        collection_type = child_type
        # rank 6: EXACT_OPERATOR_OPERANDS
        if keys in ({"arg"}, {"item"}, {"literal"}):
            pass
        elif "op" in node:
            if slots is not None:
                declared = {name for name, _ in slots}
                if keys != declared | {"op"}:
                    raise AstFail("EXACT_OPERATOR_OPERANDS", tokens)
                for name, kind in slots:
                    if kind == "SCOPE_BINDER" and not (isinstance(node[name], str) and node[name]):
                        raise AstFail("EXACT_OPERATOR_OPERANDS", tokens)
                    if kind == "NAMED_EXPRESSION_MAP" and not (isinstance(node[name], Mapping) and node[name]):
                        raise AstFail("EXACT_OPERATOR_OPERANDS", tokens)
        else:
            raise AstFail("EXACT_OPERATOR_OPERANDS", tokens)
        # rank 7: OPERATOR_IN_CLOSED_OPERATOR_LANGUAGE
        op = node.get("op")
        if "op" in node and (slots is None or op not in self.primitives):
            raise AstFail("OPERATOR_IN_CLOSED_OPERATOR_LANGUAGE", tokens)
        # rank 8: DECLARED_ARGUMENTS_ONLY
        if keys == {"arg"} and node["arg"] not in self.arguments:
            raise AstFail("DECLARED_ARGUMENTS_ONLY", tokens)
        # rank 9: LEXICAL_SCOPE_NO_SHADOW_OR_ESCAPE_ON_ACTIVE_PATH
        if keys == {"item"} and node["item"] not in scopes:
            raise AstFail("LEXICAL_SCOPE_NO_SHADOW_OR_ESCAPE_ON_ACTIVE_PATH", tokens)
        if binder is not None and binder in scopes:
            raise AstFail("LEXICAL_SCOPE_NO_SHADOW_OR_ESCAPE_ON_ACTIVE_PATH", tokens)
        # rank 10 / 11: resource limits (the measured value at this node: its depth, and the number of active
        # collection binders whose bound expression contains it; a binder node itself is measured at the current count)
        if not within_limit(self.depth_measure, depth, self.max_depth):
            raise AstFail("MAX_EXPRESSION_DEPTH_EXCEEDED", tokens)
        if not within_limit(self.nesting_measure, nesting, self.max_nesting):
            raise AstFail("MAX_LEXICAL_COLLECTION_NESTING_EXCEEDED", tokens)
        # rank 12: POINTER_LITERAL_RFC6901_VALID
        if slots is not None:
            for name, kind in slots:
                value = node.get(name)
                try:
                    if kind == "POINTER_SLOT" and isinstance(value, str):
                        pointer_tokens(value)
                    elif kind == "POINTER_ARRAY_SLOT" and not isinstance(value, Mapping):
                        if not isinstance(value, list) or not value:
                            raise ExpressionError("INVALID_JSON_POINTER")
                        for pointer in value:
                            pointer_tokens(pointer)
                except ExpressionError:
                    raise AstFail("POINTER_LITERAL_RFC6901_VALID", tokens) from None
        # rank 13: RESOLVE_ONE_USES_EXACT_VERIFICATION_UNIVERSE_TERMINAL
        if op == "RESOLVE_ONE" and node.get("universe") != {"arg": "verification_universe"}:
            raise AstFail("RESOLVE_ONE_USES_EXACT_VERIFICATION_UNIVERSE_TERMINAL", tokens)
        # rank 14: DIGEST_MODE_FIELDS_ARE_DYNAMIC_EXPRESSIONS
        if op == "DIGEST_VERIFY":
            for name in ("algorithm", "serialization", "excluded_pointers"):
                if not self._dynamic(node.get(name)):
                    raise AstFail("DIGEST_MODE_FIELDS_ARE_DYNAMIC_EXPRESSIONS", tokens)
        # rank 15..17: static typing
        return self._type_of(node, keys, op, slots, child_types, collection_type, scopes, tokens)

    def _dynamic(self, node: Any) -> bool:
        if not isinstance(node, Mapping):
            return False
        if set(node) in ({"arg"}, {"item"}):
            return True
        slots = self.docs.slots_of(node)
        if slots is None:
            return False
        return any(self._dynamic(child) for _, _, child, _ in self.expression_children(node, [], slots))

    def _underdetermined(self, slots: Any, signature: Mapping[str, Any], child_types: Mapping[str, str], tokens: list[Any]) -> None:
        """AST_TYPE_UNDERDETERMINED_FAILS_CLOSED: a narrow consumer of a branch-ambiguous JSON result."""
        for name, kind in slots:
            if (kind in ("EXPRESSION", "POINTER_SLOT", "POINTER_ARRAY_SLOT") and child_types.get(name) == AMBIGUOUS_JSON
                    and signature.get(name) not in _WIDE_OPERAND_TYPES):
                raise AstFail("AST_TYPE_UNDERDETERMINED_FAILS_CLOSED", tokens)

    def _type_of(self, node: Mapping[str, Any], keys: set[str], op: Any, slots: Any, child_types: Mapping[str, str],
                 collection_type: str, scopes: Mapping[str, str], tokens: list[Any]) -> str:
        if keys == {"arg"}:
            return self.argument_types[node["arg"]]
        if keys == {"item"}:
            return scopes[node["item"]]
        if keys == {"literal"}:
            value = node["literal"]
            if isinstance(value, bool):
                return "BOOLEAN"
            if isinstance(value, (int, float, Decimal)):
                return "JSON_NUMBER"
            if isinstance(value, str):
                return "STRING"
            if isinstance(value, list):
                return "ARRAY<JSON>"
            return "JSON_OBJECT" if isinstance(value, dict) else "JSON"
        row = self.primitives[op]
        signature = {a.get("name"): a.get("type") for a in row.get("arguments", []) if isinstance(a, Mapping)}
        if set(signature) != set(node) - {"op"}:
            raise AstFail("AST_TYPE_UNDERDETERMINED_FAILS_CLOSED", tokens)
        result_type = row.get("output_type")
        if op in ("FILTER", "PROJECT", "ALL", "ANY"):
            collection_type = self._eff(collection_type)
            if not _assignable(signature["array"], collection_type):
                raise AstFail("OPERAND_RESULT_TYPES_VALID", tokens)
            if op == "PROJECT":
                self._underdetermined(slots, signature, child_types, tokens)
                return "ARRAY<JSON_OBJECT>"
            if child_types.get("where") not in ("BOOLEAN", AMBIGUOUS_JSON):
                raise AstFail("OPERAND_RESULT_TYPES_VALID", tokens)
            self._underdetermined(slots, signature, child_types, tokens)
            return collection_type if op == "FILTER" else "BOOLEAN"
        if op == "DURATION_SECONDS" and result_type != "JSON_NUMBER":
            raise AstFail("OPERAND_RESULT_TYPES_VALID", tokens)
        if op == "RESOLVE_ONE" and (signature.get("universe") != "VERIFICATION_UNIVERSE" or result_type != "RESOLVED_OBJECT"):
            raise AstFail("OPERAND_RESULT_TYPES_VALID", tokens)
        for name, kind in slots:
            if (kind in ("EXPRESSION", "POINTER_SLOT", "POINTER_ARRAY_SLOT") and name in child_types
                    and not _assignable(signature[name], self._eff(child_types[name]))):
                raise AstFail("OPERAND_RESULT_TYPES_VALID", tokens)
        if op == "GET":
            subject_type = child_types.get("value", "JSON")
            pointer = node["pointer"]
            typer = self.docs.typers.get(subject_type)
            if typer is not None and isinstance(pointer, str):
                try:
                    return typer.type_at(pointer_tokens(pointer))
                except StaticTypeError:
                    raise AstFail("STATIC_TYPE_AT_PATH_SCHEMA_NOMINAL_AND_STRUCTURAL", tokens) from None
            if subject_type in self.docs.static_paths and isinstance(pointer, str):
                declared = self.docs.static_paths[subject_type]
                if pointer in declared:
                    return declared[pointer]
                parts = pointer_tokens(pointer)
                first = "/" + encode_pointer_token(parts[0]) if parts else ""
                if len(parts) > 1 and declared.get(first) in _DESCENDABLE:
                    return "JSON"
                raise AstFail("STATIC_TYPE_AT_PATH_SCHEMA_NOMINAL_AND_STRUCTURAL", tokens)
        if op == "COUNT" and child_types.get("array") == "VERIFICATION_UNIVERSE":
            raise AstFail("OPERAND_RESULT_TYPES_VALID", tokens)
        self._underdetermined(slots, signature, child_types, tokens)
        return result_type


@group_handler("PE-44")
def _pe44(eng: Engine) -> None:
    docs: StaticDocs = eng.static_docs  # type: ignore[attr-defined]
    conditions = {c["condition_id"]: c for c in FAMILIES["PE-44"]["conditions"]}
    for index, procedure in enumerate(docs.procedures):
        if not isinstance(procedure, Mapping):
            continue
        root = ["procedures", index]
        arguments = [a for a in procedure.get("arguments", [])] if isinstance(procedure.get("arguments"), list) else []
        assertions = procedure.get("assertions") if isinstance(procedure.get("assertions"), list) else []
        checker = AstChecker(docs, procedure)

        def first_repeat(items: Sequence[Any], key: str) -> int | None:
            seen: set[Any] = set()
            for position, item in enumerate(items):
                value = item.get(key) if isinstance(item, Mapping) else None
                if value in seen:
                    return position
                seen.add(value)
            return None

        def fail(condition: str, pointer: str, cls: str = "PROCEDURE_DECLARATION") -> PreExecFailure:
            return eng.failure("PE-44", condition, Subj(cls), Hit(pointer=pointer))

        def procedure_limit(condition: str, value: int) -> None:
            """Procedure-level measured limit (declared measurement object): invalid values fail at the condition's location."""
            measurement = PE44_MEASUREMENTS[condition]
            if not within_limit(measurement, value, docs.measured_limit(measurement)):
                raise fail(condition, _sub(conditions[condition]["location_template"], i=index))

        repeat = first_repeat(arguments, "name")
        if repeat is not None:
            raise fail("ARGUMENT_NAMES_UNIQUE", "/procedures/%d/arguments/%d" % (index, repeat))
        if isinstance(procedure.get(PE44_MEASUREMENTS["MAX_ARGUMENTS_PER_PROCEDURE_EXCEEDED"]["measured_member"]), list):
            procedure_limit("MAX_ARGUMENTS_PER_PROCEDURE_EXCEEDED", len(arguments))
        repeat = first_repeat(assertions, "assertion_id")
        if repeat is not None:
            raise fail("ASSERTION_IDS_UNIQUE", "/procedures/%d/assertions/%d" % (index, repeat))
        if isinstance(procedure.get(PE44_MEASUREMENTS["MAX_ASSERTIONS_PER_PROCEDURE_EXCEEDED"]["measured_member"]), list):
            procedure_limit("MAX_ASSERTIONS_PER_PROCEDURE_EXCEEDED", len(assertions))
        nodes = sum(checker.node_count(a.get(key)) for a in assertions if isinstance(a, Mapping) for key in ("condition", "witness"))
        procedure_limit("MAX_AST_NODES_PER_PROCEDURE_EXCEEDED", nodes)
        for position, assertion in enumerate(assertions):
            if not isinstance(assertion, Mapping):
                continue
            for key in ("condition", "witness"):
                tokens = root + ["assertions", position, key]
                try:
                    node_type = checker.visit(assertion.get(key), tokens, checker.depth_measure["root_value"], {},
                                              checker.nesting_measure["root_value"])
                    if key == "condition" and node_type != "BOOLEAN":
                        raise AstFail("ASSERTION_CONDITION_ROOTS_BOOLEAN_NO_TRUTHINESS", tokens)
                except AstFail as found:
                    raise fail(found.condition, pointer_of(found.tokens), "AST_NODE") from None


# --- PE-46: generic failure witness declaration and witness operand identities ------------------------------------
@group_handler("PE-46")
def _pe46(eng: Engine) -> None:
    docs: StaticDocs = eng.static_docs  # type: ignore[attr-defined]
    pointer = next(c for c in FAMILIES["PE-46"]["conditions"]
                   if c["condition_id"] == "GENERIC_WITNESS_DECLARATION_UNSUPPORTED")["section_pointer"]
    law = ptr_lookup(docs.metacontract, pointer)
    operand_only = law.get("operand_only_identities", []) if isinstance(law, Mapping) else []
    checker_cache: dict[int, AstChecker] = {}

    def terminals(node: Any, tokens: list[Any]):
        """Argument terminals in declared-witness first-occurrence preorder with their pointers."""
        if not isinstance(node, Mapping):
            return
        if set(node) == {"arg"}:
            yield node["arg"], tokens
            return
        slots = docs.slots_of(node)
        if slots is None:
            return
        for _, _, child, child_tokens in AstChecker.expression_children(node, tokens, slots):
            yield from terminals(child, child_tokens)

    def has_identity(spec: Mapping[str, Any] | None) -> bool:
        if spec is None:
            return False
        if spec.get("origin") == "RULE_BINDING" and isinstance(spec.get("source_constraint"), Mapping):
            return True
        return any(row.get("argument") == spec.get("name") and row.get("argument_origin") == spec.get("origin")
                   and row.get("argument_type") == spec.get("type") for row in operand_only if isinstance(row, Mapping))

    def missing_identity(_: Subj):
        for index, procedure in enumerate(docs.procedures):
            if not (isinstance(procedure, Mapping) and isinstance(procedure.get("result"), Mapping)
                    and procedure["result"].get("type") == "BOOLEAN"):
                continue
            specs = {a.get("name"): a for a in procedure.get("arguments", []) if isinstance(a, Mapping)}
            for position, assertion in enumerate(procedure.get("assertions", [])):
                if not isinstance(assertion, Mapping):
                    continue
                for name, tokens in terminals(assertion.get("witness"), ["procedures", index, "assertions", position, "witness"]):
                    if not has_identity(specs.get(name)):
                        return Hit(pointer=pointer_of(tokens))
        return None

    scan(eng, "PE-46", [Subj("PROTOCOL_SECTION"), Subj("WITNESS_OPERAND_TERMINAL")], {
        "GENERIC_WITNESS_DECLARATION_UNSUPPORTED": lambda s: Hit() if _section_digest_differs(docs.metacontract, pointer) else None,
        "MISSING_WITNESS_OPERAND_IDENTITY": missing_identity,
    })


# --- PE-48: required binding resolution -----------------------------------------------------------------------------
def _strict_typed_reference(value: Any) -> bool:
    return (isinstance(value, Mapping) and set(value) <= {"kind", "id", "version", "member_id"}
            and all(nonempty(value.get(member)) for member in IDENTITY_MEMBERS)
            and ("member_id" not in value or nonempty(value["member_id"])))


def binding_sites(docs: StaticDocs) -> list[Subj]:
    """Invariant registry order (RULE_BINDING arguments in declaration order using default_arguments), then rule
    registry order (invariant_binding.arguments in the procedure's argument order)."""
    sites: list[Subj] = []
    for index, invariant in enumerate(docs.invariants):
        procedure = docs.procedure_by_id.get(invariant.get("procedure_id")) if isinstance(invariant, Mapping) else None
        if procedure is None:
            continue
        defaults = invariant.get("default_arguments") if isinstance(invariant.get("default_arguments"), Mapping) else {}
        for argument in procedure.get("arguments", []):
            if isinstance(argument, Mapping) and argument.get("origin") == "RULE_BINDING":
                name = argument.get("name")
                present = name in defaults
                pointer = "/invariants/%d/default_arguments" % index + ("/" + encode_pointer_token(name) if present else "")
                sites.append(Subj("BINDING_SITE", site="INVARIANT_DEFAULT_ARGUMENT", argument=argument,
                                  binding=defaults[name] if present else _ABSENT, pointer=pointer))
    for index, rule in enumerate(docs.rules):
        binding = rule.get("invariant_binding") if isinstance(rule, Mapping) else None
        if not isinstance(binding, Mapping):
            continue
        invariant = docs.invariant_by_id.get(binding.get("invariant_id"))
        procedure = docs.procedure_by_id.get(invariant.get("procedure_id")) if invariant is not None else None
        if procedure is None:
            continue
        overrides = binding.get("arguments") if isinstance(binding.get("arguments"), Mapping) else {}
        defaults = invariant.get("default_arguments") if isinstance(invariant.get("default_arguments"), Mapping) else {}
        for argument in procedure.get("arguments", []):
            if not (isinstance(argument, Mapping) and argument.get("origin") == "RULE_BINDING"):
                continue
            name = argument.get("name")
            if name in overrides:
                sites.append(Subj("BINDING_SITE", site="RULE_INVARIANT_BINDING_ARGUMENT", argument=argument, binding=overrides[name],
                                  pointer="/rules/%d/invariant_binding/arguments/%s" % (index, encode_pointer_token(name))))
            elif name not in defaults:
                sites.append(Subj("BINDING_SITE", site="RULE_INVARIANT_BINDING_ARGUMENT", argument=argument, binding=_ABSENT,
                                  pointer="/rules/%d/invariant_binding/arguments" % index))
    return sites


@group_handler("PE-48")
def _pe48(eng: Engine) -> None:
    docs: StaticDocs = eng.static_docs  # type: ignore[attr-defined]
    contract = eng.load_contract()

    def constraint(s: Subj) -> Mapping[str, Any]:
        value = s.argument.get("source_constraint")
        return value if isinstance(value, Mapping) else {}

    def target(s: Subj) -> ResolvedObject | None:
        pool = eng.bound_by_ref if constraint(s).get("universe") == "BOUND_SOURCE_UNIVERSE" else eng.candidate_by_ref
        return pool.get(identity(s.binding))

    def exact(s: Subj) -> Mapping[str, Any] | None:
        found = constraint(s).get("identity_constraint")
        return found if isinstance(found, Mapping) and found.get("mode") == "EXACT_REFERENCE" else None

    def hit(test):
        def predicate(s: Subj):
            if s.binding is _ABSENT and test is not missing:
                return None
            return Hit(pointer=s.pointer) if test(s) else None
        return predicate

    def missing(s: Subj) -> bool:
        return s.binding is _ABSENT

    def not_strict(s: Subj) -> bool:
        return not _strict_typed_reference(s.binding)

    def kind_differs(s: Subj) -> bool:
        return _strict_typed_reference(s.binding) and s.binding["kind"] != constraint(s).get("expected_kind")

    def not_in_universe(s: Subj) -> bool:
        return _strict_typed_reference(s.binding) and target(s) is None

    def ineligible(s: Subj) -> bool:
        obj = target(s) if _strict_typed_reference(s.binding) else None
        if obj is None:
            return False
        c, reg = constraint(s), obj.registration
        return (reg.get("status") != c.get("status") or reg.get("classification") != c.get("classification")
                or not set(c.get("required_roles", [])).issubset(set(reg.get("roles", []))))

    def schema_mismatch(s: Subj) -> bool:
        obj = target(s) if _strict_typed_reference(s.binding) else None
        if obj is None:
            return False
        expected = constraint(s).get("expected_schema_ref", {})
        actual = obj.registration.get("schema_ref") or {}
        return identity(actual) != identity(expected) or actual.get("member_id") != expected.get("member_id")

    def member_unresolved(s: Subj) -> bool:
        obj = target(s) if _strict_typed_reference(s.binding) else None
        return obj is not None and "member_id" in s.binding and len(member_matches(obj.content, s.binding["member_id"], obj.registration)) != 1

    def exact_mismatch(s: Subj) -> bool:
        obj = target(s) if _strict_typed_reference(s.binding) else None
        rule = exact(s)
        return obj is not None and rule is not None and (
            identity(s.binding) != identity(rule.get("ref", {})) or obj.canonical_path != rule.get("canonical_path"))

    def metadata_mismatch(s: Subj) -> bool:
        obj = target(s) if _strict_typed_reference(s.binding) else None
        rule = exact(s)
        if obj is None or rule is None or obj.source_universe != "BOUND_SOURCE_UNIVERSE":
            return False
        integrity = obj.registration.get("integrity", {})
        return any(rule.get(name) != integrity.get(name) for name in ("raw_sha256", "semantic_sha256", "git_blob"))

    scan(eng, "PE-48", binding_sites(docs), {
        "BINDING_REQUIRED_ARGUMENT_MISSING": hit(missing), "BINDING_NOT_STRICT_TYPED_REFERENCE": hit(not_strict),
        "BINDING_KIND_DIFFERS_FROM_SOURCE_CONSTRAINT": hit(kind_differs),
        "BINDING_TARGET_NOT_IN_DECLARED_UNIVERSE": hit(not_in_universe),
        "BINDING_TARGET_STATUS_CLASSIFICATION_OR_ROLES_INELIGIBLE": hit(ineligible),
        "BINDING_TARGET_SCHEMA_REFERENCE_MISMATCH": hit(schema_mismatch),
        "BINDING_TARGET_SCHEMA_MEMBER_UNRESOLVED": hit(member_unresolved),
        "BINDING_EXACT_REFERENCE_OR_PATH_MISMATCH": hit(exact_mismatch),
        "BINDING_ACCEPTED_SOURCE_METADATA_MISMATCH": hit(metadata_mismatch),
    }, subject_major=True)


# --- argument environments (runtime) and PE-47: projection map value -----------------------------------------------
def bound_object(eng: Engine, argument: Mapping[str, Any], binding: Any) -> ResolvedObject:
    pool = eng.bound_by_ref if (argument.get("source_constraint") or {}).get("universe") == "BOUND_SOURCE_UNIVERSE" else eng.candidate_by_ref
    return pool[identity(binding)]


def build_reserved_values(eng: Engine) -> None:
    values: dict[str, Any] = {}
    for name, declaration in eng.reserved_declarations.items():
        source = declaration.get("profile_content_source")
        if source is not None:
            values[name] = eng.frozen_content[source["pin_pointer_tokens"][-1]][1]
        elif declaration["origin"] == "BOOTSTRAP_VERIFICATION_UNIVERSE":
            values[name] = TypedVerificationUniverse({"objects": list(eng.universe)})
        elif declaration["origin"] == "EXTERNAL_ACCEPTANCE_PROFILE":
            values[name] = eng.profile
        else:
            values[name] = external_trust_record(declaration, eng.trust)
    eng.reserved_values = values


def assemble_arguments(eng: Engine, procedure: Mapping[str, Any], refs: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a procedure's arguments from the reserved inputs or the validated rule bindings (PE-48 has passed)."""
    env: dict[str, Any] = {}
    for argument in procedure.get("arguments", []):
        name = argument["name"]
        if name in eng.reserved_declarations:
            env[name] = eng.reserved_values[name]
            continue
        binding = refs[name]
        obj = bound_object(eng, argument, binding)
        env[name] = obj.content
    return env


def invariant_refs(eng: Engine, invariant: Mapping[str, Any], rule: Mapping[str, Any] | None = None) -> dict[str, Any]:
    refs = dict(invariant.get("default_arguments", {}))
    if rule is not None:
        refs.update(rule.get("invariant_binding", {}).get("arguments", {}))
    return refs


@group_handler("PE-47")
def _pe47(eng: Engine) -> None:
    docs: StaticDocs = eng.static_docs  # type: ignore[attr-defined]
    build_reserved_values(eng)
    selected = docs.procedures[eng.selected_item_index]
    descriptor = selected["result"]["result_projection"]
    subject = Subj("SELECTED_PROJECTION_PROCEDURE", procedure=selected, descriptor=descriptor)
    environments = [assemble_arguments(eng, selected, invariant_refs(eng, invariant))
                    for invariant in docs.invariants if isinstance(invariant, Mapping)
                    and invariant.get("procedure_id") == selected["procedure_id"]]
    expected = descriptor["expected_literals"]
    baseline = descriptor["baseline"]
    map_tokens = [str(token) for token in descriptor["pointer_tokens"]]

    def facts(env: Mapping[str, Any]) -> dict[str, Any]:
        map_value = lookup(env.get(descriptor["argument"]), map_tokens)
        baseline_document = env.get(baseline["argument"])
        values = {status: lookup(baseline_document, [str(t) for t in tokens])
                  for status, tokens in baseline["status_pointer_tokens"].items()}
        return {"map": map_value, "baseline": values}

    def each(test):
        def predicate(_: Subj):
            for env in environments:
                found = test(facts(env))
                if found is not None:
                    return found
            return None
        return predicate

    def path_invalid(f):
        return Hit(map_value=None, baseline_values=None) if f["map"] is _ABSENT or any(v is _ABSENT for v in f["baseline"].values()) else None

    def baseline_type(f):
        return Hit(baseline_values=f["baseline"]) if not all(isinstance(v, str) for v in f["baseline"].values()) else None

    def baseline_literal(f):
        return Hit(baseline_values=f["baseline"]) if any(f["baseline"][k] != expected.get(k) for k in f["baseline"]) else None

    def map_type(f):
        value = f["map"]
        return Hit(map_value=value) if not (isinstance(value, Mapping) and all(isinstance(v, str) for v in value.values())) else None

    def map_keys(f):
        value = f["map"]
        bad = set(value) != set(expected) or len(value) != descriptor["mapping_cardinality"]
        return Hit(map_value=value) if bad else None

    def map_literal(f):
        value = f["map"]
        return Hit(map_value=value) if any(value[k] != expected[k] for k in expected) else None

    scan(eng, "PE-47", [subject], {
        "PROJECTION_PATH_INVALID": each(path_invalid), "BASELINE_VALUE_TYPE": each(baseline_type),
        "BASELINE_LITERAL_MISMATCH": each(baseline_literal), "MAP_VALUE_TYPE": each(map_type),
        "MAP_MISSING_OR_EXTRA_KEY": each(map_keys), "LITERAL_MISMATCH": each(map_literal)})



# ---------------------------------------------------------------------------
# Pre-execution driver: the declared stage order, then the declared groups in group_rank order.
# ---------------------------------------------------------------------------
def handler_conformance() -> None:
    """Startup proof: every declared group has exactly one handler and every predicate set matches its family."""
    declared = {tuple(group["families"]) for stage in MODEL["stage_ordering"] for group in stage["groups"]}
    if declared != set(GROUP_HANDLERS):
        raise ModelGap("GROUP_HANDLER_MISMATCH:" + repr(sorted(declared ^ set(GROUP_HANDLERS))))
    if [stage["stage"] for index, stage in sorted(STAGE_BY_INDEX.items())] != [BOOTSTRAP_ORDER[i] for i in sorted(STAGE_BY_INDEX)]:
        raise ModelGap("STAGE_ORDER_MISMATCH")
    if MODEL["totality"]["model_status"] != "TOTAL" or MODEL["totality"]["semantic"]["pending_field_rules"] != 0:
        raise ModelGap("PRE_EXECUTION_FAILURE_MODEL_NOT_TOTAL")
    ast_law_conformance()


def run_pre_execution(eng: Engine) -> None:
    """Evaluate the groups of every stage in bootstrap order; the first failure stops the evaluation (nothing later runs)."""
    for index, name in enumerate(BOOTSTRAP_ORDER):
        stage = STAGE_BY_INDEX.get(index)
        if stage is not None:
            for group in sorted(stage["groups"], key=lambda row: row["group_rank"]):
                GROUP_HANDLERS[tuple(group["families"])](eng)
            trace_stage("stage %d %s" % (index, name))
        elif name == "DERIVE_VERIFICATION_UNIVERSE_FROM_BOOTSTRAP_INPUTS":
            derive_universe(eng)
            trace_stage("universe")


def main_result(result: dict[str, Any], exit_code: int | None = None) -> int:
    def jsonable(value: Any) -> Any:
        if isinstance(value, Decimal):
            if value.is_finite() and is_decimal_integral(value) and abs(value.adjusted()) < 1000:
                return int(value)
            return float(value)
        raise TypeError(f"non-JSON result value: {type(value).__name__}")
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=jsonable))
    if exit_code is not None:
        return exit_code
    return 0 if result.get("status") == "PASS" else 1


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute ACCORD-02E4R5R4 normative procedure ASTs independently.")
    # Inputs whose absence is a declared failure (PE-01, PE-03, PE-04, PE-14) are optional at the argument level.
    parser.add_argument("--root", help="Export root containing the explicitly selected candidate artifacts.")
    parser.add_argument("--package", help="Candidate package path, relative to --root.")
    parser.add_argument("--object-registry", help="Bootstrap object registry path, relative to --root.")
    for row in PC["caller_input_precedence"]:
        flag = row["input_name"] if row["input_name"].startswith("--") else "--" + row["input_name"].replace("_", "-")
        parser.add_argument(flag, dest=input_dest(row["input_name"]))
    parser.add_argument("--invariant", action="append", dest="selected_invariants", help="Run a selected invariant (repeatable).")
    parser.add_argument("--procedure", action="append", dest="selected_procedures", help="Run a selected procedure definition (repeatable).")
    return parser


def verify(args: argparse.Namespace) -> dict[str, Any]:
    eng = Engine(args)
    run_pre_execution(eng)
    trace_stage("pre-execution complete")
    docs: StaticDocs = eng.static_docs  # type: ignore[attr-defined]
    package, metacontract, trust = eng.package, eng.metacontract, eng.trust
    candidate, candidate_by_ref, bound_sources, bound_by_ref = eng.candidate, eng.candidate_by_ref, eng.bound_sources, eng.bound_by_ref
    universe, profile = eng.universe, eng.profile
    primitive_rows, procedure_rows, invariant_rows, rule_rows = docs.primitives, docs.procedures, docs.invariants, docs.rules
    runtime_schemas = metacontract["runtime_representation"]["value_schemas"]
    vector_source = next((obj.content for obj in bound_sources if obj.ref.get("kind") == "SOURCE_VECTOR_CATALOG"), None)
    vectors = vector_source.get("vectors", []) if isinstance(vector_source, dict) else []
    axis_sets = [set(v.get("expected", {})) for v in vectors if isinstance(v, dict) and isinstance(v.get("expected"), dict)]
    metacontract_obj = candidate_by_ref[identity(package.get("metacontract_ref") or {})]
    primitive_rows_by_id = {row["primitive_id"]: row for row in primitive_rows}
    interpreter = Interpreter(primitive_rows_by_id, metacontract.get("resource_limits", {}),
                              runtime_schemas["resolved_object"], candidate_by_ref, metacontract)
    by_proc = {row["procedure_id"]: row for row in procedure_rows}
    interpreter.procedure_positions = {row["procedure_id"]: position for position, row in enumerate(procedure_rows)}
    interpreter.witness_law_owner = metacontract_obj
    invariant_by_id = {x["invariant_id"]: x for x in invariant_rows}

    selected_invariants = set(args.selected_invariants or invariant_by_id.keys())
    selected_procedures = set(args.selected_procedures or by_proc.keys())
    invariant_results: list[dict[str, Any]] = []
    procedure_results: dict[str, list[dict[str, Any]]] = {}
    # Evaluate each active invariant through its declared procedure AST and its validated bindings.
    for invariant_id, invariant in invariant_by_id.items():
        if invariant_id not in selected_invariants:
            continue
        proc_id = invariant["procedure_id"]
        if proc_id not in selected_procedures:
            continue
        proc = by_proc[proc_id]
        source_refs = invariant_refs(eng, invariant)
        env = assemble_arguments(eng, proc, source_refs)
        result = interpreter.execute(proc, env, bound_argument_identities(proc, source_refs, candidate_by_ref, bound_by_ref), trust)
        # The registered result object stays closed; the invariant association lives on the wrapper row.
        row = {"invariant_id": invariant_id, "procedure_id": proc_id, "result": result}
        invariant_results.append(row)
        procedure_results.setdefault(proc_id, []).append(row)
        if len(invariant_results) % 5 == 0:
            trace_stage(f"invariants {len(invariant_results)}")

    member_results: list[dict[str, Any]] = []
    for rule in rule_rows:
        if rule.get("declared_class") != "EXECUTABLE_CONFORMANCE_RULE":
            continue
        member = rule.get("invariant_binding", {})
        invariant_id = member.get("invariant_id")
        invariant = invariant_by_id.get(invariant_id)
        if invariant is None or invariant_id not in selected_invariants or invariant.get("procedure_id") not in selected_procedures:
            continue
        proc = by_proc[invariant["procedure_id"]]
        refs = invariant_refs(eng, invariant, rule)
        env = assemble_arguments(eng, proc, refs)
        result = interpreter.execute(proc, env, bound_argument_identities(proc, refs, candidate_by_ref, bound_by_ref), trust)
        member_results.append({"rule_id": rule.get("rule_id"), "invariant_id": invariant_id,
                               "procedure_id": proc["procedure_id"], "result": result})
    all_pass = all(x["result"].get("status") == "PASS" for x in invariant_results + member_results)
    trace_stage(f"rules {len(member_results)} and complete")
    return {
        "status": "PASS" if all_pass else "FAIL",
        "package_identity": {"id": package.get("package_id"), "version": package.get("package_version"),
                             "digest": eng.package_recomputed_digest()},
        "trust_result": trust,
        "counts": {"candidate_universe": len(candidate), "bound_source_universe": len(bound_sources),
                   "verification_universe": len(universe), "primitives": len(primitive_rows), "procedures": len(procedure_rows),
                   "invariants": len(invariant_results), "member_rules": len(member_results),
                   "accepted_vectors": len(vectors), "expectation_axes": len(axis_sets[0]) if axis_sets else 0},
        "procedure_results": procedure_results,
        "invariant_results": invariant_results,
        "member_rule_results": member_results,
        "accepted_expectation": {"vector_count": len(vectors), "axes": len(axis_sets[0]) if axis_sets else 0,
                                 "axis_ids": sorted(axis_sets[0]) if axis_sets else []},
    }


def entrypoint() -> int:
    parser = build_cli()
    args = parser.parse_args()
    try:
        derivation_conformance()
        handler_conformance()
        result = verify(args)
    except PreExecFailure as failure:
        result = failure.result
    except VerificationError as exc:
        result = {"status": "FAIL", "stage": exc.stage, "code": exc.code, "witness": exc.witness}
    except Exception as exc:  # implementation-internal (PE-50..PE-53): never a registered normative result
        import traceback
        traceback.print_exc(file=sys.stderr)
        return main_result({"status": "IMPLEMENTATION_ERROR", "implementation_error": {"class": type(exc).__name__}}, 70)
    return main_result(result)


if __name__ == "__main__":
    sys.exit(entrypoint())
