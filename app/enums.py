import enum


class Category(enum.Enum):
    dress = "dress"
    tops = "tops"
    outer = "outer"
    bottoms = "bottoms"


class Color(enum.Enum):
    white = "white"
    black = "black"
    red = "red"
    blue = "blue"
    beige = "beige"


class Season(enum.Enum):
    spring = "spring"
    summer = "summer"
    autumn = "autumn"
    winter = "winter"
