import functools
import os
import re
import timeit
import decimal
from decimal import Decimal

from typing import List

from bs4 import BeautifulSoup, Tag
import requests

f1040_url = "https://www.irs.gov/instructions/i1040gi"
f1040_file = "irs1040.html"

p17_url = "https://www.irs.gov/publications/p17"
p17_file = "p17.html"


class Bracket:
    def __init__(self, lower: Decimal, upper: Decimal, rate: Decimal):
        self.lower = lower
        self.upper = upper
        self.rate = rate
    
    def __str__(self):
        return "[{} - {} @ {}%]".format(self.lower, self.upper, self.rate)
    
    def __repr__(self):
        return "Bracket({}, {}, {})".format(self.lower, self.upper, self.rate)


class Schedule:
    def __init__(self, brackets: List[Bracket]):
        self.brackets = brackets
    
    def __str__(self):
        return "(\n" + "\n".join(str(b) for b in self.brackets) + "\n)"
    
    def __repr__(self):
        return "Schedule({})".format(self.brackets)


def get_text(url: str, filename: str):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf8") as file_handle:
            return file_handle.read()
    else:
        page = requests.get(url)
        with open(filename, "w", encoding="utf8") as file_handle:
            file_handle.write(page.text)
        return page.text


def find_schedule(soup: Tag, name: str):
    return soup.find(string=re.compile(name)).find_next("table")


def parse_schedule(table: Tag):
    rate_regex = re.compile(r"(\d+(?:\.\d+)?)%")
    brackets = []
    for row in table.tbody('tr'):
        data = row('td')
        lower = Decimal(data[0].string.strip().lstrip('$').replace(',', ''))
        try:
            upper = Decimal(data[1].string.strip().lstrip('$').replace(',', ''))
        except decimal.InvalidOperation:
            upper = Decimal('Infinity')
        rate = Decimal(rate_regex.search(data[2].string).group(1))
        brackets.append(Bracket(lower, upper, rate))
    return Schedule(brackets)


text = get_text(p17_url, p17_file)
soup = BeautifulSoup(text, "lxml")
book = soup.find(class_="book")
# soup = BeautifulSoup(text, "html.parser")

tax_schedules = book.find(string=re.compile(r"^\d{4} Tax Rate Schedules$")).find_parent("div", class_="section")

tax_schedule_single = find_schedule(tax_schedules, "Schedule X")
tax_schedule_married_joint = find_schedule(tax_schedules, "Schedule Y-1")
tax_schedule_married_separate = find_schedule(tax_schedules, "Schedule Y-2")
tax_schedule_head = find_schedule(tax_schedules, "Schedule Z")

single = parse_schedule(tax_schedule_single)
married_joint = parse_schedule(tax_schedule_married_joint)
married_separate = parse_schedule(tax_schedule_married_separate)
head = parse_schedule(tax_schedule_head)

print("Single:", single)
print("Married joint:", married_joint)
print("Married separate:", married_separate)
print("Head of household:", head)

# if __name__ == "__main__":
#     main()
