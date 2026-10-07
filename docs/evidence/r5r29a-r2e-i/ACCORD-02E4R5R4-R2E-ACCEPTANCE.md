# ACCORD-02E4R5R4 R2e Acceptance

## Status and scope

**R2e is accepted in the local canonical candidate** only for the exact frozen object and governed behaviours recorded in [the machine-readable manifest](accord-02e4r5r4-r2e-acceptance-manifest.json). This record does not accept any later R5R29A phase or broaden the established R2e law.

The staged 56-file law tree has SHA-256 `0d2f567c65d5a9a91d86c12faabb21655cc6b2724d5539d799ef7325bf734ce8`. Its canonical 56-file installation, with the adjudicated evaluator overlay, has SHA-256 `7485da2f29c13fb7d7cd9e365de85c573fcc96fe28e2e272b03e70c9d0105fd2`. The staged package has semantic SHA-256 `4b343600039c73f3ee4bc64edbb4abdd2912b18941966d51fcd25360901697f1` and remains byte-for-byte frozen; the embedded candidate status was not edited during acceptance.

## Authority and verification

The adjudication evidence manifest is `7bc846732fbeaaa20a6b1f6b6c560c30c194fcea4267876f62243670fff5dc73` and its report is `6f3518067ac6ccafdda64b7ad1772541d571e3029812e89705bb06dda97b2833`. The C2 evidence manifest is `2587805b38bc6b39b1b69275f1ec9b5e3b22e15aeda74204da3cd7e80213fad9`. The installed PRIMARY evaluator is `8facf456d00d72a4eb3217a3ef624cc99d7f351cc7626b66366371dafd0dca04`. The retained INDEPENDENT evaluator is `69230e1c5afbafd5ea653ac7b3d68934ed13991d7c061e9a46d2673478782ad1` and remains audit evidence, not the executable canonical evaluator.

The installation map is SHA-256 `8f829d40630d1d25ed1b998c152bc3494b652885142e2e086291589a6074c3d4`. It records all 56 source-to-destination actions: two additions, twelve replacements, and forty-two byte-identical files. Verification checked 44 registered semantic digests, 23 schema meta-validations, 23 registered instances, all 40 invariants and 42 bound rules, 46 candidate objects, 112 C2 schema cases (including all 69 direct R2e schema cases), and the three governed integrity cases. The installed PRIMARY outputs match the frozen C2 PRIMARY outputs on all 115 cases. Deep regression reached schema depth 2000 and runtime-value depth 1200. Mutations ran only on isolated copies. The clean full output and both mutation raw outputs are byte-identical to C2 PRIMARY evidence.

R2e-I historically received a 52-file neutral package; C2 later verified the complete 56-file staged tree. PRIMARY and INDEPENDENT differ in numeric CLI failure exit codes (2 and 1), which the staged law does not govern. These facts remain part of the acceptance record.

## Repository disposition

This is a local branch acceptance. Protected `main` and remote refs are left unchanged. The containing Git commit, tree, parent, committed paths, and any acceptance tag target are recorded in repository metadata and the final installation report outside the self-hashing acceptance content. The next phase requires separate authorization.
