from bot.training.genetic_trainer import Gene

g = Gene(0, 2)
print(str(g))
print(g.lower_bound)
g.value -= 10
print(str(g.value))
