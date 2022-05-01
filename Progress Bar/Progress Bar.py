import colorama
import math

def progress_bar(progress, total, load_color=colorama.Fore.YELLOW, end_color=colorama.Fore.GREEN):
	percent = 100 * (float(progress) / float(total))
	bar = "█" * int(percent) + "-" * (100 - int(percent))
	print(load_color + f"\r|{bar}|{percent:.2f}%", end="\r")
	if (progress==total):
	    print(end_color + f"\r|{bar}|{percent:.2f}%", end="\r")


numbers = [x * 5 for x in range(2000,3000)]
result = []

progress_bar(0,len(numbers))
for i, x in enumerate(numbers):
    result.append(math.factorial(x))
    progress_bar(i+1,len(numbers))
print(colorama.Fore.RESET + "\r")