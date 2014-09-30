//chmod u=rwx,go=xr,+s

#include <unistd.h>
#include <iostream>
#include <stdlib.h>
#include <string>
#include <sys/types.h>

int main(int argc, char *argv[]) {
	std::string default_directory("/share/apps/gorque/");
	std::string command = default_directory + "gorque.py -l | less";
	// std::cout << command;
	setuid(0);
	system(command.c_str());
	return 0;
}