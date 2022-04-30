import colorama #pip install colorama

def progress_bar(progress, total, load_color=colorama.Fore.YELLOW, end_color=colorama.Fore.GREEN):
	percent = 100 * (float(progress) / float(total))
	bar = "█" * int(percent) + "-" * (100 - int(percent))
	print(load_color + f"\r|{bar}|{percent.2f}%", end="\r")
	if (progress==total):
	  print(end_color + f"\r|{bar}|{percent.2f}%", end="\r"
	print(colorama.Fore.RESET)
