# Deferred quantum ML extension

Status: NOT STARTED. Finish the classical research and review its findings and methodology with the learner before starting quantum lessons or implementation. The classical project must remain independently runnable and publishable, without quantum dependencies. Current classical phases continue in their established order.

## Learning contract

Explain → Build → Show → Ask → Check → Continue, with a pre-implementation checkpoint for each major phase. Teach accessible mathematics just in time. Wait for answers, give hints for mistakes, and revisit weak reasoning. Do not generate the whole extension in advance. Update `docs/learning_log.md` and `docs/concepts.md` as lessons occur. Show experimental results to the learner before giving interpretations. Preserve feature branches, PR review, and explicit owner merge approval. Run checks locally; do not enable or dispatch GitHub Actions without an explicit request.

## Research question

Do near-term quantum machine-learning approaches provide measurable advantages over classical machine-learning models for financial-market prediction under leakage-safe out-of-sample evaluation?

Define hypotheses, comparisons, budgets, and evaluation criteria before experiments. Do not assume superiority. “No quantum advantage was observed” is a valid outcome. Separate predictive, economic, and computational improvements. Simulator performance alone does not demonstrate a quantum computational speedup.

## Ordered extension phases

1. **Complete classical foundation.** Finish data, features, leakage checks, expanding-window validation, Logistic Regression, Random Forest, XGBoost, LightGBM, execution/backtesting, costs, CAGR/Sharpe/Sortino/drawdown, robustness, and statistical analysis. Explain findings and quiz the learner before advancing. Preserve an independently publishable classical report.
2. **Quantum fundamentals.** Teach bits/qubits, states, superposition, measurement, amplitudes, bra-ket notation, basic linear algebra, gates, Hadamard, rotations, CNOT, entanglement, and circuits. Start with accessible mathematics; no quantum code before understanding checks.
3. **QML fundamentals.** Teach classical-to-quantum data encoding, angle encoding, feature maps, kernels, variational/parameterised circuits, classifiers, classical optimisation, and hybrid training. Explain quantum-kernel/QSVM-style classification and VQC, then quiz before implementation.
4. **Formal research design.** Refine the question and prerecord hypotheses before any model comparison. Specify what evidence would and would not justify each kind of advantage claim.
5. **Prepare shared financial data.** Reuse the underlying classical dataset and leakage-safe methodology. Investigate feature selection, dimensionality reduction, scaling, and reduced training subsets only with scientific justification. Fit preprocessing on training data only. Document every classical/quantum difference; use matched classical comparisons when quantum budgets require reduced data/features. Teach feature count versus qubit requirements.
6. **Isolated environment.** Select one primary framework (Qiskit/Qiskit Machine Learning or PennyLane) after checking the tools then available. Use simulators initially and optional, isolated dependencies. Requested layout: `src/quantum/`, `tests/quantum/`, `config/quantum_experiment.yaml`, `results/quantum/`, `figures/quantum/`. Resolve packaging and the existing `configs/` naming convention explicitly at this checkpoint. Do not create the module or install packages now. No paid hardware is required.
7. **Quantum kernel.** Teach feature maps, kernel meaning, and which computation is quantum versus classical. Pipeline: financial features → training-fitted scaling/selection → quantum feature map → quantum kernel → classical SVM → prediction. Check understanding, then implement and evaluate out of sample.
8. **VQC.** Teach ansatz, parameters, encoding, measurement, losses, classical optimisation, hybrid training, and introductory barren plateaus. Pipeline: financial features → encoding → parameterised circuit → measurement → classical optimiser → updated parameters → prediction. Quiz before final experiments.
9. **Matched comparison.** Compare all four classical models, quantum kernel, and VQC under equivalent out-of-sample evaluation where possible. ML metrics: accuracy, balanced accuracy, F1, ROC-AUC, log loss, Brier score. Financial metrics: CAGR, Sharpe, Sortino, maximum drawdown, turnover, net return. Computational metrics: training/inference time, qubits, circuit depth, trainable parameters, simulator/runtime requirements. Document probability estimation/calibration without test leakage before using probability metrics.
10. **Costs.** Route quantum predictions through the same execution/backtest code at 0/5/10/25 bps. Determine whether predictive differences survive economically; accuracy alone is not quantum advantage.
11. **Robustness.** Vary period, costs, thresholds, feature count, qubit count, depth, and training size within declared budgets. Discuss instability, multiple comparisons, and data snooping.
12. **Optional hardware.** Only after correct simulator experiments, assess a small accessible real-hardware run. Teach noise, decoherence, gate/measurement errors, and NISQ. Compare hardware and simulator if feasible. Hardware is not a completion requirement; no paid hardware is authorised by this plan.
13. **Learner-led interpretation.** Show results first. Ask which model leads in prediction, Sharpe, drawdown, costs, and compute; ask whether advantage is demonstrated and what limitations remain. Critique the learner's interpretation afterward.
14. **Extended paper.** Preserve the classical report and create an extended version with background, QML, feature maps, kernel method, VQC, setup, matched results, computational cost, costs, robustness, simulation limits, and an evidence-based advantage discussion. Use only real verified academic references and actual results. Possible title: *Beyond Accuracy: Classical and Quantum Machine Learning for Financial Market Prediction Under Realistic Market Frictions*.
15. **Career outputs.** Once research is complete, update README, report, LinkedIn, CV bullets, and interview notes to demonstrate software engineering, ML, quant finance, and quantum understanding. No exaggerated claims. Follow the existing learner-first LinkedIn checkpoint.
16. **Interview practice.** Ask one question at a time on qubits, superposition, feature maps, kernels, VQC, hybrid training, simulators, NISQ, observed advantage or lack thereof, financial ML difficulty, leakage, accuracy versus trading performance, and next research. Challenge weak reasoning and teach rather than supply memorised scripts.

## Current boundary

This document authorises planning, not skipping learning gates. Quantum concepts remain NOT STARTED. Classical benchmark work remains the active task. The standalone classical deliverable need not wait for the quantum extension.
