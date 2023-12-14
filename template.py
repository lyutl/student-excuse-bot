import random

import pandas as pd
import numpy as np

START = 'Здравствуйте, NAME!\n'
END = '\nС уважением, SENDER.'

PLACEHOLDERS = ['CLASS', 'DATE', 'NAME', 'SENDER']

df = pd.read_csv('student_excuse.csv')

REASONS = set(df['Reason'])
POSTPONES = set(df['Postponement'])
PEOPLE = set(df['Peepl'])
CONST_LIST = [REASONS, POSTPONES, PEOPLE]
COLUMN_NAMES = list(df.columns[1:])

COLUMN_DICT = dict(zip(COLUMN_NAMES, CONST_LIST))


# reason is from the user --> get postponement options --> user chooses --> get people options
class Option:
    def __init__(self):
        self.reason_options = []
        self.people_options = []

    def get_reason_options(self, post_choice: str) -> set:
        self.reason_options = set(df.query(f"{COLUMN_NAMES[1]}=='{post_choice}'")[COLUMN_NAMES[0]])
        return self.reason_options

    def get_ppl_options(self, post_choice: str, reason_choice: str) -> set:
        self.people_options = set(df.query(f"{COLUMN_NAMES[1]}=='{post_choice}'").query(
            f"{COLUMN_NAMES[0]}=='{reason_choice}'")[COLUMN_NAMES[2]])
        return self.people_options


class Template:
    def __init__(self):
        self.right_templates = []

    def get_by_choice(self, choice: str, column: tuple) -> None:
        for el in column[-1]:
            if choice == el:
                templates = df.query(f"{column[0]}=='{el}'")["Template"]
                if self.right_templates:
                    self.right_templates = list(np.intersect1d(self.right_templates, templates))
                else:
                    self.right_templates.append(templates)

    def random_choice(self) -> str:
        random_template = random.choice(self.right_templates)
        return random_template


def change_placeholder(template: str, choices: dict) -> str:
    for ph in PLACEHOLDERS:
        if ph in template:
            template = template.replace(ph, choices.get(ph.lower()))
    return template
