class EducationalQuiz: 
    def __init__(self, quiz_id, topic):
        self.quiz_id = quiz_id
        self.topic = topic
        self.questions_list = []
        
    def add_question(self, question):
        self.questions_list.append(question)
        
    def get_questions(self):
        return self.questions_list
    
    def calculate_score(self, submitted_answers):
        score = 0
        for question in self.questions_list:
            selected_answer = submitted_answers.get(question.question_id)
            if selected_answer == question.correct_answer:
                score += 1
        return score