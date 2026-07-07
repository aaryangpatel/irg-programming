import matplotlib.pyplot as plt
import numpy as np

methods = ['PlaidX', 'Your Ranking']
scores_manual = [0.44, 0.59]
errors_manual = [0.03, 0.02]
scores_llm = [0.80, 0.82]
errors_llm = [0.05, 0.05]

x = np.arange(len(methods))  # positions
width = 0.35  # width of bars

fig, ax = plt.subplots()

# Grouped bars: Manual evaluation
rects1 = ax.bar(x - width/2, scores_manual, width, yerr=errors_manual, capsize=5, label='Manual')

# Grouped bars: LLM evaluation
rects2 = ax.bar(x + width/2, scores_llm, width, yerr=errors_llm, capsize=5, label='LLM')

ax.set_ylabel('NDCG@20')
ax.set_title('Evaluation Measure by Method and Ground Truth')
ax.set_xticks(x)
ax.set_xticklabels(methods)
ax.legend()

plt.tight_layout()
plt.show()
