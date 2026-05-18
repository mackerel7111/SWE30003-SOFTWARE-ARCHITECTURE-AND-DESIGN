class QuizQuestion:
    def __init__(self, question_id, question_text, answer_options, correct_answer, feedback):
        self.question_id = question_id
        self.question_text = question_text
        self.answer_options = answer_options  # List of possible answers
        self.correct_answer = correct_answer  # The correct answer (should be one of the options)
        self.feedback = feedback  # Feedback to provide after answering
        
    def check_answer(self, selected_answer):
        return selected_answer == self.correct_answer
    
    def get_feedback(self):
        return self.feedback.get_explanation()
        
        