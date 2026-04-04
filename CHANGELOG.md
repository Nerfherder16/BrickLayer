# Changelog

All notable changes documented here.
Maintained automatically by BrickLayer post-commit hook and karen agent.

---

## 1.0.0 (2026-04-04)


### Features

* add bl-verifier agent — BrickLayer installation health checker ([99f310f](https://github.com/Nerfherder16/BrickLayer/commit/99f310f2a15ee542e8c969f1a437de81ff9ab733))
* add pass@N metrics, test files, Charlie playbooks (tasks 12/25/32 progress) ([f8d8f9a](https://github.com/Nerfherder16/BrickLayer/commit/f8d8f9a5a0c4a116d80fb91a76c5e95943e39919))
* **agents:** add fail-closed defaults and confidence gating to reviewer agents (task 15/32) ([6ddb840](https://github.com/Nerfherder16/BrickLayer/commit/6ddb840f90a0fdcddaf3be0612acaf5fc1f31d37))
* **agents:** add H0/H1/prediction triad template to question-designer-bl2 (task 9/32) ([2ff9210](https://github.com/Nerfherder16/BrickLayer/commit/2ff921050807f18dbd14460baddc32aa0c2ad853))
* **agents:** add LOKI reflect phase and competing hypotheses protocol to trowel (task 22/32) ([8b0b133](https://github.com/Nerfherder16/BrickLayer/commit/8b0b1336f19089153885601e0112e61bfe3eb3a4))
* **agents:** add tdd-orchestrator agent ([e4babef](https://github.com/Nerfherder16/BrickLayer/commit/e4babeff27fa91278b9b5f772fd79d6bd2d2594b))
* **agents:** add triggers/tools fields to SKILL.md frontmatter standard (task 2/32) ([8692fec](https://github.com/Nerfherder16/BrickLayer/commit/8692fecb4b0a22c9b8292c75fb92bb4ea3af5f48))
* **agents:** add verifier agent for dual spec-compliance verification ([76671c8](https://github.com/Nerfherder16/BrickLayer/commit/76671c80ec47624f87e7ed13302594c76365a7b4))
* **bricklayer-meta:** add Wave 3 questions Q7.1-Q7.9 ([e425fcc](https://github.com/Nerfherder16/BrickLayer/commit/e425fccf6670ef99b7382a45ecd2fb3e96f0e216))
* **bricklayer-meta:** complete Wave 3 — Q7.1-Q7.9 findings + synthesis ([a80f4ec](https://github.com/Nerfherder16/BrickLayer/commit/a80f4ec9eed69ea3bea97c568a920667e3bff016))
* **bricklayer-meta:** Wave 4 findings + synthesis (Q8.1-Q8.5) ([f53c768](https://github.com/Nerfherder16/BrickLayer/commit/f53c7685e6c4e27dc567394e8d6e4f9801bb7815))
* **claims-board:** async human escalation via .autopilot/claims.json + HUD indicator ([026bf41](https://github.com/Nerfherder16/BrickLayer/commit/026bf414265e6c836422baad03b115b9d8f200cd))
* **consensus:** wire masonry_review_consensus into code-reviewer for conflict resolution ([81abd77](https://github.com/Nerfherder16/BrickLayer/commit/81abd77af635c02d0bbf1c183837cd542dc3e32b))
* **dev-execution:** complete Tracks A-F of Ruflo-parity build capability ([aa22d1f](https://github.com/Nerfherder16/BrickLayer/commit/aa22d1fc52109d78e79ace859a93f4588177da3b))
* **ema-loop:** end-to-end EMA training pipeline — collector + Stop hook ([2f387c7](https://github.com/Nerfherder16/BrickLayer/commit/2f387c7cd679c6144eea1791bf103d0ffc772188))
* **handoff2:** implement connective tissue tasks H1-H7 ([45bd1eb](https://github.com/Nerfherder16/BrickLayer/commit/45bd1ebff7b5c7bfbd1b475ebfa0c8da8f358ef4))
* **hooks:** add 5 anti-pattern detection checks to masonry-agent-onboard.js (task 4/32) ([149d751](https://github.com/Nerfherder16/BrickLayer/commit/149d751323d8c4cc0ee588c411005d5152bdcf5f))
* **hooks:** add masonry-mortar-enforcer PreToolUse:Agent hook ([408ddfb](https://github.com/Nerfherder16/BrickLayer/commit/408ddfb106891d380ae0e07c0085239e4a39b18a))
* **hooks:** add masonry-secret-scanner.js PreToolUse hook with 12 secret patterns (task 5/32) ([d2f4e54](https://github.com/Nerfherder16/BrickLayer/commit/d2f4e54b03be877a9aa861335f79a6ab16e347ec))
* **hooks:** add prompt router + teammate-idle auto-assign; update dev roadmap ([31fc2aa](https://github.com/Nerfherder16/BrickLayer/commit/31fc2aa32820094ac296a0f04f843ce8848e7d60))
* **hooks:** Phase 1 complete — phase checkpoints + git-nerd integration ([54df26a](https://github.com/Nerfherder16/BrickLayer/commit/54df26a18c1b0a18500109fd5f9a175b8499047f))
* **hooks:** Phase 1 wave 1 — pre-edit backup, strategy flag, build-guard cleanup ([10f99c0](https://github.com/Nerfherder16/BrickLayer/commit/10f99c0097294eb8d553b92e68bf2cd9fa013730))
* **hooks:** Phase 1 wave 2 — telemetry, agent-complete, strategy injection, phase checkpoints ([59e356d](https://github.com/Nerfherder16/BrickLayer/commit/59e356dd7e2f5fb53759ce3388b282d5e282fd5d))
* implement roadmap priorities 1-6 from bricklayer-meta synthesis ([258f546](https://github.com/Nerfherder16/BrickLayer/commit/258f54610857672a2596fc7008e0ca13174fc147))
* **masonry:** Phase 1–2 — Python package setup, routing, scoring, training pipeline ([#10](https://github.com/Nerfherder16/BrickLayer/issues/10)) ([ab02b41](https://github.com/Nerfherder16/BrickLayer/commit/ab02b41014832ba0507ab062f598244882fbe8c7))
* **mcp:** Phase 6 complete — 9 new dev execution tools in masonry-mcp.js ([7ab6d59](https://github.com/Nerfherder16/BrickLayer/commit/7ab6d59acbfc946492506f53beccfee125cb3a1e))
* merge bricklayer-v2/mar24-parallel — Phase 2-3 training + reasoning + hook fixes ([24ae351](https://github.com/Nerfherder16/BrickLayer/commit/24ae351e0fb9fc272c7d8f676098ef8fd8e6bafa))
* **mid-build-recall:** sync Recall patterns every 5 completed tasks during build ([8ef5c5e](https://github.com/Nerfherder16/BrickLayer/commit/8ef5c5e866c9e9ae841702f6b60ec3b5c66d03cf))
* **mortar:** apply A1 simplification — 5-condition binary routing ([ccd96f0](https://github.com/Nerfherder16/BrickLayer/commit/ccd96f0a9329c2164f222bf6965640141fb93b9a))
* **p3-task2:** add masonry_optimization_status to Python MCP server ([8ce696d](https://github.com/Nerfherder16/BrickLayer/commit/8ce696d16c61deaa8400933d39ad8e29dbb3576b))
* **pagerank-trigger:** Stop hook runs pagerank.py hourly fire-and-forget ([39c0aa9](https://github.com/Nerfherder16/BrickLayer/commit/39c0aa9d3b39f135b4da70fb235d4c52c3f92fe6))
* **pattern-decay:** masonry_pattern_decay tool + fix pagerank-trigger args ([36ffa4b](https://github.com/Nerfherder16/BrickLayer/commit/36ffa4bf7015e44072def8da80074bd5f2e05708))
* **phase2:** add masonry_verify_7point comment stub to mcp server ([a339b22](https://github.com/Nerfherder16/BrickLayer/commit/a339b2227550a8d5ed90900f6a64e2b1171e85de))
* **phase2:** add masonry_verify_7point tests and vitest config update ([44e5fec](https://github.com/Nerfherder16/BrickLayer/commit/44e5feca96da318515e11f091b2ca3d0883398fa))
* **phase2:** add senior-developer agent (Gap 7 escalation tier 2) ([563b4cc](https://github.com/Nerfherder16/BrickLayer/commit/563b4cccf1c3c7967b456e4869019af7eab613e9))
* **phase2b:** Bayesian confidence updates in post-task hook + confidence in training export ([570c306](https://github.com/Nerfherder16/BrickLayer/commit/570c30675b280b8dbbd6d0b15bbc2934ba15643b))
* **phase2b:** swarm compaction survival + PatternRecord confidence + masonry_pattern_decay tool ([4b36e74](https://github.com/Nerfherder16/BrickLayer/commit/4b36e74575a502ac8bde749cc92bbe9e564eae5f))
* **phase2:** implement masonry_verify_7point 7-check quality gate (Gap 6) ([f7cc9b3](https://github.com/Nerfherder16/BrickLayer/commit/f7cc9b3ef7a76eb84941ef349e4cf4afd39ebbdf))
* **phase3-wave1:** complete Wave 1 — training pipeline, ReasoningBank, knowledge graph ([9542766](https://github.com/Nerfherder16/BrickLayer/commit/954276620a902f0a5d1614a6fda2747bf09a7ab0))
* **phase3-wave1:** init training pipeline + reasoning modules (partial) ([6c05ef2](https://github.com/Nerfherder16/BrickLayer/commit/6c05ef2b6c36ee175497bc44e4e6bd8b83543fa8))
* **phase3-wave2:** MCP tools + session-start ReasoningBank integration ([00a76e9](https://github.com/Nerfherder16/BrickLayer/commit/00a76e936b970411cf6940f203b67448888380aa))
* **phase5:** complete build queue — 22 domain agents, 7 marketing skills, golden examples, 8 interaction states ([fbb8e47](https://github.com/Nerfherder16/BrickLayer/commit/fbb8e47c89659327d75890975090c570213a5ac6))
* **phase8:** complete Ruflo gap closures — daemon workers, trust scoring, doctor tool ([253e79d](https://github.com/Nerfherder16/BrickLayer/commit/253e79d135b82c445006b36d53874cf19b756098))
* **phases1-5:** T3/T6/T7/T11/T13/T14/T18/T29/T31 — session 3 progress ([7bbfd06](https://github.com/Nerfherder16/BrickLayer/commit/7bbfd0636f8904960cb53c78590a4511f468c398))
* **post-task:** fire-and-forget ReasoningBank graph recording on task success ([d5aa7e3](https://github.com/Nerfherder16/BrickLayer/commit/d5aa7e34baf8ca24841fe31f9cb91778ff9da0ed))
* **pre-edit:** backup hook for instant single-file rollback in build/fix mode ([447e873](https://github.com/Nerfherder16/BrickLayer/commit/447e873714b08e56f7d09fd88054667398623478))
* **reasoning:** local HNSW fallback for ReasoningBank — works without Qdrant ([1f69601](https://github.com/Nerfherder16/BrickLayer/commit/1f696017555bdb1d55512a8fd1e4688ee36b43df))
* **repo-research:** add repo-researcher agent + AGENTS-COLLECTION analysis ([beb0610](https://github.com/Nerfherder16/BrickLayer/commit/beb0610c85dc2cab3e7bbcba6cb2ea7e83e07de6))
* Ruflo Tier 1+2 — SPARC phases, consensus, claims, depends_on, EMA pipeline ([ce4e9fa](https://github.com/Nerfherder16/BrickLayer/commit/ce4e9fa7232674e7c4ccb4e4baa25c904ffda1ce))
* **schemas:** add GradeConfidence enum to FindingPayload with auto-population (task 10/32) ([e8b018e](https://github.com/Nerfherder16/BrickLayer/commit/e8b018ef1309d9c93559e9f2e303db80261cf63c))
* **score-trigger:** auto-spawn DSPy optimization every 50 scored examples ([6e15a81](https://github.com/Nerfherder16/BrickLayer/commit/6e15a81309d3cb4f22ac2dd726e19b2282317422))
* **sft:** optimize agents, augment corpus to 898 records, fix pipeline bugs ([cb8f2e5](https://github.com/Nerfherder16/BrickLayer/commit/cb8f2e56a841756300b8761e9d1a4ddc10157e02))
* **sparc-consensus:** SPARC phases + consensus builder fully wired ([a68d996](https://github.com/Nerfherder16/BrickLayer/commit/a68d996d0cb608ffbc235e5f25f064ddd75c02ed))
* **T1-T5:** masonry hardening — LLM router, session locks, hooks manifest, e2e diagnostics ([62f814d](https://github.com/Nerfherder16/BrickLayer/commit/62f814dd65cecc5f35dfd69962264be426cc2ab3))
* **T1.3:** harden LLM router — env var model, retry, preflight check ([d68dcc4](https://github.com/Nerfherder16/BrickLayer/commit/d68dcc4d5ea18468b1bce8fc7ef54f41dedcfeea))
* **T4.1:** mark session ownership lock system complete in FIX_PLAN ([fd6f5c5](https://github.com/Nerfherder16/BrickLayer/commit/fd6f5c527ea0330285fbb0a30f49169355ef3624))
* **tier1:** Ruflo gap closures — verification agent, effort routing, ultralearn, map, context curator ([447d5e0](https://github.com/Nerfherder16/BrickLayer/commit/447d5e073fee8be77d6398af4d99a95cf677b8e7))
* **tier3-partial:** graph.py updates + HNSW test + topology module (in-progress) ([b571fe4](https://github.com/Nerfherder16/BrickLayer/commit/b571fe4033ccbb6491db3065ab8c20c8f34c6e04))
* **tier3:** P3.2 HNSW fallback + P3.3 PageRank + P3.4 topology selector ([42426fd](https://github.com/Nerfherder16/BrickLayer/commit/42426fd4be56ebe4d437394fc9de097fe889e8d2))
* **trowel:** add Recall health check at campaign start (Wave 1 only) ([d1642a8](https://github.com/Nerfherder16/BrickLayer/commit/d1642a81af36a560d7b6b21ebe4ede56acffc226))
* **trowel:** add Recall health check at Wave 1 cold-start ([1fa0ba1](https://github.com/Nerfherder16/BrickLayer/commit/1fa0ba197e4f34700d69f0e86bdb30602ecd0024))
* **wave-15:** complete Wave 15 — research-analyst 0.93, E12.1-live-15 fixed ([b333c5d](https://github.com/Nerfherder16/BrickLayer/commit/b333c5d293f6430b34106baf7277474c0494dd1f))
* **wave-41:** close P-w40.1 convergence trap + unblock karen optimization ([837b2ad](https://github.com/Nerfherder16/BrickLayer/commit/837b2ad05c385dd77395bbd37420e0553155e1ed))
* **wave-42:** find corpus/eval sizing risks, fix P4 slot collision ([7d45f64](https://github.com/Nerfherder16/BrickLayer/commit/7d45f64c94f1c72fb381226348f4c6328677089a))
* **wave-43:** fix pre-optimization safety issues + expose research-analyst corpus gap ([e0c2782](https://github.com/Nerfherder16/BrickLayer/commit/e0c27820435406a6f8e0000af99ca78ee58b7f58))


### Bug Fixes

* **build-guard:** skip legacy-build warning when progress.json status is COMPLETE ([3f46918](https://github.com/Nerfherder16/BrickLayer/commit/3f4691851a36862563baaf2221b6d4244775f606))
* **ci:** fix release-please — use googleapis action, simple release type ([95cb59b](https://github.com/Nerfherder16/BrickLayer/commit/95cb59bf65a5d0bdf908719d9b7b1a3171e218e9))
* **e2e:** add missing mortar.md sentinel headings + update agent_registry ([5b0de17](https://github.com/Nerfherder16/BrickLayer/commit/5b0de17a55a93ff0026333919b224d8d322b48d6))
* **e2e:** sync template rough-in to BL2.0, patch trowel Recall sections ([de0786a](https://github.com/Nerfherder16/BrickLayer/commit/de0786a6c542fd65c9757d5d650ee3f6c992ab60))
* **eval_sft:** align karen eval with training data format ([e89e63c](https://github.com/Nerfherder16/BrickLayer/commit/e89e63c2a64ee68176f1b953970d88439bc0cb49))
* **findings:** correct E14.6 karen result and E14.8 crash details ([dc7075c](https://github.com/Nerfherder16/BrickLayer/commit/dc7075cb824255d1fdfce29962a1d3b47a5b7f9e))
* **finetune:** reduce seq_len and batch size to fit RTX 3060 VRAM ([b1344d3](https://github.com/Nerfherder16/BrickLayer/commit/b1344d37e52234f69f12ffb9213d313585bd2269))
* **handoff2:** wire 4 gaps — template mortar system-status, trowel regression check, training_ready.flag fallback, decay_conflicting_memories call site ([82363ca](https://github.com/Nerfherder16/BrickLayer/commit/82363caa745df2fe53a91e15d7ff6f4bf1204b10))
* **hooks:** fix Stop hook JSON schema + context-monitor only blocks when dirty ([7d8962d](https://github.com/Nerfherder16/BrickLayer/commit/7d8962d81b5beb238c8b885c4786530b608063c2))
* **hooks:** use local node_modules/.bin instead of npx for prettier/eslint ([cf3ab7f](https://github.com/Nerfherder16/BrickLayer/commit/cf3ab7fb4515bef803d4655ce1b6baa1b36f156a))
* **karen:** restore full agent definition lost during optimization ([0381660](https://github.com/Nerfherder16/BrickLayer/commit/038166024b68eacd1e15b90cc68f11b9a83f48b4))
* **masonry:** pass signature arg through improve_agent loop to optimize_with_claude ([2638280](https://github.com/Nerfherder16/BrickLayer/commit/263828065c4492e9d268789076e2027c87212e7d))
* **mcp:** async exit race + Recall health endpoint + pulse hook wired ([1b7d7b5](https://github.com/Nerfherder16/BrickLayer/commit/1b7d7b58ed89d37eea7ef8d96bf8c8cd24be4135))
* **mortar:** enforce delegation via tool restrictions and explicit Agent tool calls ([5ef4c43](https://github.com/Nerfherder16/BrickLayer/commit/5ef4c438d44893221de60812b79071c6cc53f691))
* **p1+p3:** register senior-developer in registry + fix test_server.py sys.path ([2f61dd2](https://github.com/Nerfherder16/BrickLayer/commit/2f61dd20f70a913b962404a20778bc8f5a6038d7))
* **phase3-wave1:** minor cleanup to graph.py and pagerank.py ([a63216e](https://github.com/Nerfherder16/BrickLayer/commit/a63216e4d5f9dc2b142608aefd66abda6175f0fb))
* **recall:** correct API endpoints and payload schema across all workers ([0de2d61](https://github.com/Nerfherder16/BrickLayer/commit/0de2d61f66b49d09ed5e292cab573c9bffc2503c))
* **session-start:** daemon auto-start fires on more project types + writes pid files ([99fda6a](https://github.com/Nerfherder16/BrickLayer/commit/99fda6a8c37521fb4ccb3f3a7bb6cc4dd90c8a8c))
* **stop-guard:** generate descriptive auto-commit messages instead of generic ones ([5d21ff8](https://github.com/Nerfherder16/BrickLayer/commit/5d21ff81525b732e9c163b5ffe54912a025557cc))
* **swarm:** wire TeammateIdle + swarm_init + unblock general-purpose spawns ([39d9a41](https://github.com/Nerfherder16/BrickLayer/commit/39d9a41817142a577029f20c2b34b22e7af083eb))
* **tests:** split fake Stripe test key to avoid push protection false positive ([b075244](https://github.com/Nerfherder16/BrickLayer/commit/b07524475a3d5fced4cc854df20422e8522b1e15))
* **training-export:** default to ~/.mas/training.db when BRICKLAYER_TRAINING_DB not set ([8a39373](https://github.com/Nerfherder16/BrickLayer/commit/8a39373b5aa06da09303c9aa91f369aff64b60d2))
* **training:** switch finetune_lxc to Qwen2.5-7B-Instruct (ungated) ([c13c55f](https://github.com/Nerfherder16/BrickLayer/commit/c13c55f2022eeb83c7bad952047a18d76306b6a5))
* **training:** switch to Qwen2.5-3B, fix PYTORCH_CUDA_ALLOC_CONF placement ([fe0231c](https://github.com/Nerfherder16/BrickLayer/commit/fe0231c5073f547a40ad3c6895d437bb9933dad6))
* untrack runtime files + README improvements ([261823c](https://github.com/Nerfherder16/BrickLayer/commit/261823ce30d1fc6a9e6fe04ba578c700f4d2282a))
* **windows:** windowsHide on all detached spawns + remove completed agents from statusline ([43c5822](https://github.com/Nerfherder16/BrickLayer/commit/43c5822a01a5e787c3692ba922980fcec5c1bfbe))

## 1.0.0 (2026-04-04)


### Features

* add bl-verifier agent — BrickLayer installation health checker ([99f310f](https://github.com/Nerfherder16/BrickLayer/commit/99f310f2a15ee542e8c969f1a437de81ff9ab733))
* add pass@N metrics, test files, Charlie playbooks (tasks 12/25/32 progress) ([f8d8f9a](https://github.com/Nerfherder16/BrickLayer/commit/f8d8f9a5a0c4a116d80fb91a76c5e95943e39919))
* **agents:** add fail-closed defaults and confidence gating to reviewer agents (task 15/32) ([6ddb840](https://github.com/Nerfherder16/BrickLayer/commit/6ddb840f90a0fdcddaf3be0612acaf5fc1f31d37))
* **agents:** add H0/H1/prediction triad template to question-designer-bl2 (task 9/32) ([2ff9210](https://github.com/Nerfherder16/BrickLayer/commit/2ff921050807f18dbd14460baddc32aa0c2ad853))
* **agents:** add LOKI reflect phase and competing hypotheses protocol to trowel (task 22/32) ([8b0b133](https://github.com/Nerfherder16/BrickLayer/commit/8b0b1336f19089153885601e0112e61bfe3eb3a4))
* **agents:** add tdd-orchestrator agent ([e4babef](https://github.com/Nerfherder16/BrickLayer/commit/e4babeff27fa91278b9b5f772fd79d6bd2d2594b))
* **agents:** add triggers/tools fields to SKILL.md frontmatter standard (task 2/32) ([8692fec](https://github.com/Nerfherder16/BrickLayer/commit/8692fecb4b0a22c9b8292c75fb92bb4ea3af5f48))
* **agents:** add verifier agent for dual spec-compliance verification ([76671c8](https://github.com/Nerfherder16/BrickLayer/commit/76671c80ec47624f87e7ed13302594c76365a7b4))
* **bricklayer-meta:** add Wave 3 questions Q7.1-Q7.9 ([e425fcc](https://github.com/Nerfherder16/BrickLayer/commit/e425fccf6670ef99b7382a45ecd2fb3e96f0e216))
* **bricklayer-meta:** complete Wave 3 — Q7.1-Q7.9 findings + synthesis ([a80f4ec](https://github.com/Nerfherder16/BrickLayer/commit/a80f4ec9eed69ea3bea97c568a920667e3bff016))
* **bricklayer-meta:** Wave 4 findings + synthesis (Q8.1-Q8.5) ([f53c768](https://github.com/Nerfherder16/BrickLayer/commit/f53c7685e6c4e27dc567394e8d6e4f9801bb7815))
* **claims-board:** async human escalation via .autopilot/claims.json + HUD indicator ([026bf41](https://github.com/Nerfherder16/BrickLayer/commit/026bf414265e6c836422baad03b115b9d8f200cd))
* **consensus:** wire masonry_review_consensus into code-reviewer for conflict resolution ([81abd77](https://github.com/Nerfherder16/BrickLayer/commit/81abd77af635c02d0bbf1c183837cd542dc3e32b))
* **dev-execution:** complete Tracks A-F of Ruflo-parity build capability ([aa22d1f](https://github.com/Nerfherder16/BrickLayer/commit/aa22d1fc52109d78e79ace859a93f4588177da3b))
* **ema-loop:** end-to-end EMA training pipeline — collector + Stop hook ([2f387c7](https://github.com/Nerfherder16/BrickLayer/commit/2f387c7cd679c6144eea1791bf103d0ffc772188))
* **handoff2:** implement connective tissue tasks H1-H7 ([45bd1eb](https://github.com/Nerfherder16/BrickLayer/commit/45bd1ebff7b5c7bfbd1b475ebfa0c8da8f358ef4))
* **hooks:** add 5 anti-pattern detection checks to masonry-agent-onboard.js (task 4/32) ([149d751](https://github.com/Nerfherder16/BrickLayer/commit/149d751323d8c4cc0ee588c411005d5152bdcf5f))
* **hooks:** add masonry-mortar-enforcer PreToolUse:Agent hook ([408ddfb](https://github.com/Nerfherder16/BrickLayer/commit/408ddfb106891d380ae0e07c0085239e4a39b18a))
* **hooks:** add masonry-secret-scanner.js PreToolUse hook with 12 secret patterns (task 5/32) ([d2f4e54](https://github.com/Nerfherder16/BrickLayer/commit/d2f4e54b03be877a9aa861335f79a6ab16e347ec))
* **hooks:** add prompt router + teammate-idle auto-assign; update dev roadmap ([31fc2aa](https://github.com/Nerfherder16/BrickLayer/commit/31fc2aa32820094ac296a0f04f843ce8848e7d60))
* **hooks:** Phase 1 complete — phase checkpoints + git-nerd integration ([54df26a](https://github.com/Nerfherder16/BrickLayer/commit/54df26a18c1b0a18500109fd5f9a175b8499047f))
* **hooks:** Phase 1 wave 1 — pre-edit backup, strategy flag, build-guard cleanup ([10f99c0](https://github.com/Nerfherder16/BrickLayer/commit/10f99c0097294eb8d553b92e68bf2cd9fa013730))
* **hooks:** Phase 1 wave 2 — telemetry, agent-complete, strategy injection, phase checkpoints ([59e356d](https://github.com/Nerfherder16/BrickLayer/commit/59e356dd7e2f5fb53759ce3388b282d5e282fd5d))
* implement roadmap priorities 1-6 from bricklayer-meta synthesis ([258f546](https://github.com/Nerfherder16/BrickLayer/commit/258f54610857672a2596fc7008e0ca13174fc147))
* **mcp:** Phase 6 complete — 9 new dev execution tools in masonry-mcp.js ([7ab6d59](https://github.com/Nerfherder16/BrickLayer/commit/7ab6d59acbfc946492506f53beccfee125cb3a1e))
* merge bricklayer-v2/mar24-parallel — Phase 2-3 training + reasoning + hook fixes ([24ae351](https://github.com/Nerfherder16/BrickLayer/commit/24ae351e0fb9fc272c7d8f676098ef8fd8e6bafa))
* **mid-build-recall:** sync Recall patterns every 5 completed tasks during build ([8ef5c5e](https://github.com/Nerfherder16/BrickLayer/commit/8ef5c5e866c9e9ae841702f6b60ec3b5c66d03cf))
* **mortar:** apply A1 simplification — 5-condition binary routing ([ccd96f0](https://github.com/Nerfherder16/BrickLayer/commit/ccd96f0a9329c2164f222bf6965640141fb93b9a))
* **p3-task2:** add masonry_optimization_status to Python MCP server ([8ce696d](https://github.com/Nerfherder16/BrickLayer/commit/8ce696d16c61deaa8400933d39ad8e29dbb3576b))
* **pagerank-trigger:** Stop hook runs pagerank.py hourly fire-and-forget ([39c0aa9](https://github.com/Nerfherder16/BrickLayer/commit/39c0aa9d3b39f135b4da70fb235d4c52c3f92fe6))
* **pattern-decay:** masonry_pattern_decay tool + fix pagerank-trigger args ([36ffa4b](https://github.com/Nerfherder16/BrickLayer/commit/36ffa4bf7015e44072def8da80074bd5f2e05708))
* **phase2:** add masonry_verify_7point comment stub to mcp server ([a339b22](https://github.com/Nerfherder16/BrickLayer/commit/a339b2227550a8d5ed90900f6a64e2b1171e85de))
* **phase2:** add masonry_verify_7point tests and vitest config update ([44e5fec](https://github.com/Nerfherder16/BrickLayer/commit/44e5feca96da318515e11f091b2ca3d0883398fa))
* **phase2:** add senior-developer agent (Gap 7 escalation tier 2) ([563b4cc](https://github.com/Nerfherder16/BrickLayer/commit/563b4cccf1c3c7967b456e4869019af7eab613e9))
* **phase2b:** Bayesian confidence updates in post-task hook + confidence in training export ([570c306](https://github.com/Nerfherder16/BrickLayer/commit/570c30675b280b8dbbd6d0b15bbc2934ba15643b))
* **phase2b:** swarm compaction survival + PatternRecord confidence + masonry_pattern_decay tool ([4b36e74](https://github.com/Nerfherder16/BrickLayer/commit/4b36e74575a502ac8bde749cc92bbe9e564eae5f))
* **phase2:** implement masonry_verify_7point 7-check quality gate (Gap 6) ([f7cc9b3](https://github.com/Nerfherder16/BrickLayer/commit/f7cc9b3ef7a76eb84941ef349e4cf4afd39ebbdf))
* **phase3-wave1:** complete Wave 1 — training pipeline, ReasoningBank, knowledge graph ([9542766](https://github.com/Nerfherder16/BrickLayer/commit/954276620a902f0a5d1614a6fda2747bf09a7ab0))
* **phase3-wave1:** init training pipeline + reasoning modules (partial) ([6c05ef2](https://github.com/Nerfherder16/BrickLayer/commit/6c05ef2b6c36ee175497bc44e4e6bd8b83543fa8))
* **phase3-wave2:** MCP tools + session-start ReasoningBank integration ([00a76e9](https://github.com/Nerfherder16/BrickLayer/commit/00a76e936b970411cf6940f203b67448888380aa))
* **phase5:** complete build queue — 22 domain agents, 7 marketing skills, golden examples, 8 interaction states ([fbb8e47](https://github.com/Nerfherder16/BrickLayer/commit/fbb8e47c89659327d75890975090c570213a5ac6))
* **phase8:** complete Ruflo gap closures — daemon workers, trust scoring, doctor tool ([253e79d](https://github.com/Nerfherder16/BrickLayer/commit/253e79d135b82c445006b36d53874cf19b756098))
* **phases1-5:** T3/T6/T7/T11/T13/T14/T18/T29/T31 — session 3 progress ([7bbfd06](https://github.com/Nerfherder16/BrickLayer/commit/7bbfd0636f8904960cb53c78590a4511f468c398))
* **post-task:** fire-and-forget ReasoningBank graph recording on task success ([d5aa7e3](https://github.com/Nerfherder16/BrickLayer/commit/d5aa7e34baf8ca24841fe31f9cb91778ff9da0ed))
* **pre-edit:** backup hook for instant single-file rollback in build/fix mode ([447e873](https://github.com/Nerfherder16/BrickLayer/commit/447e873714b08e56f7d09fd88054667398623478))
* **reasoning:** local HNSW fallback for ReasoningBank — works without Qdrant ([1f69601](https://github.com/Nerfherder16/BrickLayer/commit/1f696017555bdb1d55512a8fd1e4688ee36b43df))
* **repo-research:** add repo-researcher agent + AGENTS-COLLECTION analysis ([beb0610](https://github.com/Nerfherder16/BrickLayer/commit/beb0610c85dc2cab3e7bbcba6cb2ea7e83e07de6))
* Ruflo Tier 1+2 — SPARC phases, consensus, claims, depends_on, EMA pipeline ([ce4e9fa](https://github.com/Nerfherder16/BrickLayer/commit/ce4e9fa7232674e7c4ccb4e4baa25c904ffda1ce))
* **schemas:** add GradeConfidence enum to FindingPayload with auto-population (task 10/32) ([e8b018e](https://github.com/Nerfherder16/BrickLayer/commit/e8b018ef1309d9c93559e9f2e303db80261cf63c))
* **score-trigger:** auto-spawn DSPy optimization every 50 scored examples ([6e15a81](https://github.com/Nerfherder16/BrickLayer/commit/6e15a81309d3cb4f22ac2dd726e19b2282317422))
* **sft:** optimize agents, augment corpus to 898 records, fix pipeline bugs ([cb8f2e5](https://github.com/Nerfherder16/BrickLayer/commit/cb8f2e56a841756300b8761e9d1a4ddc10157e02))
* **sparc-consensus:** SPARC phases + consensus builder fully wired ([a68d996](https://github.com/Nerfherder16/BrickLayer/commit/a68d996d0cb608ffbc235e5f25f064ddd75c02ed))
* **T1-T5:** masonry hardening — LLM router, session locks, hooks manifest, e2e diagnostics ([62f814d](https://github.com/Nerfherder16/BrickLayer/commit/62f814dd65cecc5f35dfd69962264be426cc2ab3))
* **T1.3:** harden LLM router — env var model, retry, preflight check ([d68dcc4](https://github.com/Nerfherder16/BrickLayer/commit/d68dcc4d5ea18468b1bce8fc7ef54f41dedcfeea))
* **T4.1:** mark session ownership lock system complete in FIX_PLAN ([fd6f5c5](https://github.com/Nerfherder16/BrickLayer/commit/fd6f5c527ea0330285fbb0a30f49169355ef3624))
* **tier1:** Ruflo gap closures — verification agent, effort routing, ultralearn, map, context curator ([447d5e0](https://github.com/Nerfherder16/BrickLayer/commit/447d5e073fee8be77d6398af4d99a95cf677b8e7))
* **tier3-partial:** graph.py updates + HNSW test + topology module (in-progress) ([b571fe4](https://github.com/Nerfherder16/BrickLayer/commit/b571fe4033ccbb6491db3065ab8c20c8f34c6e04))
* **tier3:** P3.2 HNSW fallback + P3.3 PageRank + P3.4 topology selector ([42426fd](https://github.com/Nerfherder16/BrickLayer/commit/42426fd4be56ebe4d437394fc9de097fe889e8d2))
* **trowel:** add Recall health check at campaign start (Wave 1 only) ([d1642a8](https://github.com/Nerfherder16/BrickLayer/commit/d1642a81af36a560d7b6b21ebe4ede56acffc226))
* **trowel:** add Recall health check at Wave 1 cold-start ([1fa0ba1](https://github.com/Nerfherder16/BrickLayer/commit/1fa0ba197e4f34700d69f0e86bdb30602ecd0024))
* **wave-15:** complete Wave 15 — research-analyst 0.93, E12.1-live-15 fixed ([b333c5d](https://github.com/Nerfherder16/BrickLayer/commit/b333c5d293f6430b34106baf7277474c0494dd1f))
* **wave-41:** close P-w40.1 convergence trap + unblock karen optimization ([837b2ad](https://github.com/Nerfherder16/BrickLayer/commit/837b2ad05c385dd77395bbd37420e0553155e1ed))
* **wave-42:** find corpus/eval sizing risks, fix P4 slot collision ([7d45f64](https://github.com/Nerfherder16/BrickLayer/commit/7d45f64c94f1c72fb381226348f4c6328677089a))
* **wave-43:** fix pre-optimization safety issues + expose research-analyst corpus gap ([e0c2782](https://github.com/Nerfherder16/BrickLayer/commit/e0c27820435406a6f8e0000af99ca78ee58b7f58))


### Bug Fixes

* **build-guard:** skip legacy-build warning when progress.json status is COMPLETE ([3f46918](https://github.com/Nerfherder16/BrickLayer/commit/3f4691851a36862563baaf2221b6d4244775f606))
* **ci:** fix release-please — use googleapis action, simple release type ([95cb59b](https://github.com/Nerfherder16/BrickLayer/commit/95cb59bf65a5d0bdf908719d9b7b1a3171e218e9))
* **e2e:** add missing mortar.md sentinel headings + update agent_registry ([5b0de17](https://github.com/Nerfherder16/BrickLayer/commit/5b0de17a55a93ff0026333919b224d8d322b48d6))
* **e2e:** sync template rough-in to BL2.0, patch trowel Recall sections ([de0786a](https://github.com/Nerfherder16/BrickLayer/commit/de0786a6c542fd65c9757d5d650ee3f6c992ab60))
* **eval_sft:** align karen eval with training data format ([e89e63c](https://github.com/Nerfherder16/BrickLayer/commit/e89e63c2a64ee68176f1b953970d88439bc0cb49))
* **findings:** correct E14.6 karen result and E14.8 crash details ([dc7075c](https://github.com/Nerfherder16/BrickLayer/commit/dc7075cb824255d1fdfce29962a1d3b47a5b7f9e))
* **finetune:** reduce seq_len and batch size to fit RTX 3060 VRAM ([b1344d3](https://github.com/Nerfherder16/BrickLayer/commit/b1344d37e52234f69f12ffb9213d313585bd2269))
* **handoff2:** wire 4 gaps — template mortar system-status, trowel regression check, training_ready.flag fallback, decay_conflicting_memories call site ([82363ca](https://github.com/Nerfherder16/BrickLayer/commit/82363caa745df2fe53a91e15d7ff6f4bf1204b10))
* **hooks:** fix Stop hook JSON schema + context-monitor only blocks when dirty ([7d8962d](https://github.com/Nerfherder16/BrickLayer/commit/7d8962d81b5beb238c8b885c4786530b608063c2))
* **hooks:** use local node_modules/.bin instead of npx for prettier/eslint ([cf3ab7f](https://github.com/Nerfherder16/BrickLayer/commit/cf3ab7fb4515bef803d4655ce1b6baa1b36f156a))
* **karen:** restore full agent definition lost during optimization ([0381660](https://github.com/Nerfherder16/BrickLayer/commit/038166024b68eacd1e15b90cc68f11b9a83f48b4))
* **masonry:** pass signature arg through improve_agent loop to optimize_with_claude ([2638280](https://github.com/Nerfherder16/BrickLayer/commit/263828065c4492e9d268789076e2027c87212e7d))
* **mcp:** async exit race + Recall health endpoint + pulse hook wired ([1b7d7b5](https://github.com/Nerfherder16/BrickLayer/commit/1b7d7b58ed89d37eea7ef8d96bf8c8cd24be4135))
* **mortar:** enforce delegation via tool restrictions and explicit Agent tool calls ([5ef4c43](https://github.com/Nerfherder16/BrickLayer/commit/5ef4c438d44893221de60812b79071c6cc53f691))
* **p1+p3:** register senior-developer in registry + fix test_server.py sys.path ([2f61dd2](https://github.com/Nerfherder16/BrickLayer/commit/2f61dd20f70a913b962404a20778bc8f5a6038d7))
* **phase3-wave1:** minor cleanup to graph.py and pagerank.py ([a63216e](https://github.com/Nerfherder16/BrickLayer/commit/a63216e4d5f9dc2b142608aefd66abda6175f0fb))
* **recall:** correct API endpoints and payload schema across all workers ([0de2d61](https://github.com/Nerfherder16/BrickLayer/commit/0de2d61f66b49d09ed5e292cab573c9bffc2503c))
* **session-start:** daemon auto-start fires on more project types + writes pid files ([99fda6a](https://github.com/Nerfherder16/BrickLayer/commit/99fda6a8c37521fb4ccb3f3a7bb6cc4dd90c8a8c))
* **stop-guard:** generate descriptive auto-commit messages instead of generic ones ([5d21ff8](https://github.com/Nerfherder16/BrickLayer/commit/5d21ff81525b732e9c163b5ffe54912a025557cc))
* **swarm:** wire TeammateIdle + swarm_init + unblock general-purpose spawns ([39d9a41](https://github.com/Nerfherder16/BrickLayer/commit/39d9a41817142a577029f20c2b34b22e7af083eb))
* **tests:** split fake Stripe test key to avoid push protection false positive ([b075244](https://github.com/Nerfherder16/BrickLayer/commit/b07524475a3d5fced4cc854df20422e8522b1e15))
* **training-export:** default to ~/.mas/training.db when BRICKLAYER_TRAINING_DB not set ([8a39373](https://github.com/Nerfherder16/BrickLayer/commit/8a39373b5aa06da09303c9aa91f369aff64b60d2))
* **training:** switch finetune_lxc to Qwen2.5-7B-Instruct (ungated) ([c13c55f](https://github.com/Nerfherder16/BrickLayer/commit/c13c55f2022eeb83c7bad952047a18d76306b6a5))
* **training:** switch to Qwen2.5-3B, fix PYTORCH_CUDA_ALLOC_CONF placement ([fe0231c](https://github.com/Nerfherder16/BrickLayer/commit/fe0231c5073f547a40ad3c6895d437bb9933dad6))
* untrack runtime files + README improvements ([261823c](https://github.com/Nerfherder16/BrickLayer/commit/261823ce30d1fc6a9e6fe04ba578c700f4d2282a))
* **windows:** windowsHide on all detached spawns + remove completed agents from statusline ([43c5822](https://github.com/Nerfherder16/BrickLayer/commit/43c5822a01a5e787c3692ba922980fcec5c1bfbe))

## [Unreleased]

---

## [2026-04-04]

### Added
- `[feat]` Learning loop: `toolPatternPromote` (+20% headroom) and `toolPatternDemote` (-15%, floor 0.1) in `masonry/src/tools/impl-patterns.js`
- `[feat]` MCP tool definitions for `masonry_pattern_promote` and `masonry_pattern_demote` in `schema-advanced.js`; dispatch cases in `masonry-mcp.js`
- `[feat]` `masonry-build-outcome.js` — PostToolUse:Write hook watches `.autopilot/progress.json` for DONE/FAILED transitions and calls promote/demote; infers agent type from `[mode:X]` annotations
- `[feat]` Session-start pattern decay — `context-data.js` auto-runs `toolPatternDecay` at every session start; injects top-5 agents by confidence score as context hint
- `[feat]` 108 new tests across 4 test files covering learning loop behavior
- `[feat]` Add tmux terminal profiles for Tim and Nick in VS Code (`fd3a7a33`)
- `[feat]` Add Proxmox skill; update homelab skill with ubuntu-claude; fix deploy-claude.sh atomic write (`aaecd2d7`)
- `[feat]` Sync mcpServers from ~/.claude.json via deploy-claude.sh (`a3f54e53`)
- `[feat]` Sync ~/.claude assets — skills, plugins, monitors, deploy script (`317479d6`)

### Fixed
- `[fix]` codevvOS: fix recall_client endpoint calls (`f89d562a`)
- `[fix]` masonry-prompt-inject: add auth header and fix threshold (`d8597571`)
- `[fix]` Redact secrets from mcp-servers.json (`c4450772`)
- `[fix]` Restore masonry/bin/masonry-mcp.js (deleted in cleanup) (`024ab87d`)

### Changed
- `[docs]` CLAUDE.md delegation rules rewritten — dev tasks now route to rough-in directly; Mortar is entry point for campaigns/research and docs only (`cd3dc405`)
- `[docs]` Update network map: ubuntu-claude Tailscale SSH, code.streamy.tube backend, workspace path (`32338569`)

### Automated
- `[autopilot]` masonry-mortar-enforcer.js updated to allow direct specialist spawns from main session, aligning with new routing rules (`cd3dc405`)
- `[autopilot]` masonry-prompt-router.js: added `@agent-name:` self-invoke bypass — any prompt starting with `@agentname:` skips all routing and spawns that agent directly (`cd3dc405`)

---

## [2026-04-03]

### Added
- `[feat]` Terminal tab titles — Tim=octoface, Nick=diamond; color-coded terminal profiles (`4d58259d`, `83b1be5e`, `05eb4434`)
- `[feat]` User attribution — terminal profiles + CLAUDE_USER tagging in Recall (`50dffee3`)
- `[feat]` git-sync script for cross-machine repo sync (`16879647`)
- `[feat]` Automation recommendations from codebase analysis (`cca491f6`)

### Fixed
- `[fix]` Nick terminal icon — diamond → ruby (valid codicon) (`465b5688`)
- `[fix]` codevvOS Docker build + LXC deployment fixes (`9a732e70`)
- `[fix]` version-check uses dynamic path, works on any machine (`5cd6772f`)

### Changed
- `[chore]` Preserve executable bit on scripts (`d5977def`)
- `[chore]` Gitignore .claude settings backups to prevent secret leaks (`9b819bc1`)
- `[chore]` Expand developer skills registry + symlink Windows skills to WSL (`e79b24c1`)
- `[chore]` Expand agent tool access and enforce jcodemunch-first pattern (`9ba722ca`)
- `[chore]` Versioning + VS Code daily check (`8e46b03b`)

---

## [Wave 14 — Evolve] (complete as of 2026-04-02)

### Engine Fixes
- `bl/tmux/core.py` — per-spawn gate (`BL_GATE_FILE`) added
- `bl/tmux/pane.py` — `capture-pane` uses `$TMUX_PANE`
- `bl/runners/correctness.py` — Linux + Windows path regex
- `bl/recall_bridge.py` — dead `decay_conflicting_memories()` removed
- `bl/config.py` — `recall_src` reads `RECALL_SRC` env var

### Masonry Hook Fixes
- `masonry-mortar-enforcer.js` — `BL_GATE_FILE` env var
- `masonry-routing-gate.js` — `BL_GATE_FILE` env var
- `session/mortar-gate.js` — dynamic loader from `agent_registry.yml` + frontmatter

### Agent Fixes
- `mortar.md` — WSL-portable paths
- `trowel.md` — `RECALL_HOST` env var
- `bl-verifier.md`, `e2e.md` — WSL paths

---

## [Wave 1 — Initial Campaign]

- Campaign initialized
