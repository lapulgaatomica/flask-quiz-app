from random import randint, choice
from . import db
from .models import Question
from faker import Faker

def questions(count=1000):
    """
    Function adds fake questions to the database during development

    return: None
    """
    fake = Faker()
    for i in range(count):
        question = Question(
            body=fake.text(max_nb_chars=70),
            a=fake.word(),
            b=fake.word(),
            c=fake.word(),
            d=fake.word(),
            e=fake.word(),
            correct=choice(['a', 'b', 'c', 'd', 'e']),
            course_id=randint(1, 5),
            user_id=randint(2, 4)
        )
        db.session.add(question)
    db.session.commit()
    