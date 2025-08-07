import os

sample_question_and_answer = [
    {
        "question": "What are the types of hyperparathyroidism?",
        "answer_path": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "./md/answer_1.md")
        ),
    },
    {
        "question": "Explain about liver injury?",
        "answer_path": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "./md/answer_2.md")
        ),
    },
    {
        "question": "Explain me the Structure of Kidney?",
        "answer_path": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "./md/answer_3.md")
        ),
    },
    {
        "question": "What are the Clinical features of carcinoma lip?",
        "answer_path": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "./md/answer_4.md")
        ),
    },
    {
        "question": "What are the Causes of Dysphagia?",
        "answer_path": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "./md/answer_5.md")
        ),
    },
]
