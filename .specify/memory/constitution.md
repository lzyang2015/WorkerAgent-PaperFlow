<!--
SYNC IMPACT REPORT
Version Change: 0.0.0 -> 1.0.0
Modified Principles: All (Initial Definition)
Added Sections: None
Removed Sections: None
Templates Requiring Updates: ✅ None (Templates are generic)
Follow-up: None
-->
# PaperFlow Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### I. 中文优先 (Language First)
<!-- Example: I. Library-First -->
除了代码逻辑本身，全过程必须使用中文。这包括需求文档、设计文档、调研资料、以及详细的代码注释。
<!-- Example: Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries -->

### II. Python生态 (Python Ecosystem)
<!-- Example: II. CLI Interface -->
项目必须使用Python编码。必须在当前目录下建立Python虚拟环境（`.venv` 或 `venv`）来支持隔离的开发和测试环境。
<!-- Example: Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats -->

### III. 测试驱动与覆盖 (Test-First & Coverage)
<!-- Example: III. Test-First (NON-NEGOTIABLE) -->
测试优先（TDD）。必须编写详细的单元测试，单元测试必须覆盖所有的条件分支。执行过程中每完成一个任务都需要测试，只有通过后才能进行下一步。
<!-- Example: TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced -->

### IV. 可扩展设计 (Extensible Design)
<!-- Example: IV. Integration Testing -->
系统设计需要充分考虑可扩展性。避免硬编码，通过抽象和接口设计支持未来的功能扩展。
<!-- Example: Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas -->

### V. 详尽注释 (Comprehensive Comments)
<!-- Example: V. Observability, VI. Versioning & Breaking Changes, VII. Simplicity -->
代码必须有详细的注释。类、函数、关键变量、条件或循环语句均需加上中文注释，解释代码的意图和逻辑。
<!-- Example: Text I/O ensures debuggability; Structured logging required; Or: MAJOR.MINOR.BUILD format; Or: Start simple, YAGNI principles -->

### VI. 完备的用户故事 (Complete User Stories)
需要编写完善的User Story，不仅包含正常流程，更要详细考虑并描述失败的情况（Failure Cases）该如何处理。

## 流程与规范 (Process & Standards)
<!-- Example: Additional Constraints, Security Requirements, Performance Standards, etc. -->

1.  **任务执行**: 每个任务完成后必须立即运行测试，确保通过。
2.  **环境管理**: 确保虚拟环境激活，所有依赖记录在 `requirements.txt` 或 `pyproject.toml` 中。

## Governance
<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

本宪章规定了项目的核心开发准则。任何代码提交（PR）和设计文档都必须遵循以上原则。修改本宪章需要团队共识并更新版本号。

**Version**: 1.0.0 | **Ratified**: 2026-01-23 | **Last Amended**: 2026-01-23
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
