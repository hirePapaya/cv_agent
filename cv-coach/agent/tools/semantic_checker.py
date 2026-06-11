##from transformers import pipeline

##classifier = pipeline(
##    "zero-shot-classification",
##    model="facebook/bart-large-mnli"
##)


##def evaluate_rule(text: str, hypothesis: str):
##    result = classifier(
##        text,
##        [hypothesis],
##        multi_label=True
##    )

##    return {
##        "hypothesis": hypothesis,
##        "score": result["scores"][0]
##    }