import enum


class Category(enum.Enum):
    dress = "dress"
    tops = "tops"
    outer = "outer"
    bottoms = "bottoms"
    dress = "dress"
    shoes = "shoes"
    bag = "bag"
    other = "other"
    accessory = "accessory"


class Color(enum.Enum):
    white = "white"
    black = "black"
    red = "red"
    blue = "blue"
    beige = "beige"
    gray = "gray"
    yellow = "yellow"
    pink = "pink"
    green = "green"
    purple = "purple"
    brown = "brown"
    other = "other"


class Season(enum.Enum):
    spring = "spring"
    summer = "summer"
    autumn = "autumn"
    winter = "winter"
