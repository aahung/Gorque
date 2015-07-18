//chmod u=rwx,go=xr,+s

#include <unistd.h>
#include <iostream>
#include <stdlib.h>
#include <string>
#include <string.h>
#include <sys/types.h>
#include "parameter.h"

int main(int argc, char *argv[]) {
	std::string default_directory(GODIR);
	std::string command;
	if (argc == 1)
		command = default_directory + "/gorque.py -l";
	else if (strcmp(argv[1], "-a") == 0)
		command = default_directory + "/gorque.py -a | less";
	else
		std::cout << "Usage: gostat [-a]\n";
	setuid(0);
	system(command.c_str());
	return 0;
}