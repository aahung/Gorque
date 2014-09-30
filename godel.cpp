//chmod u=rwx,go=xr,+s

#include <unistd.h>
#include <iostream>
#include <stdlib.h>
#include <string>
#include <sys/types.h>

int main(int argc, char *argv[]) {
	std::string default_directory("/share/apps/gorque/");
	if ( argc != 2 ) {
    	std::cout << "usage: <script file>";
    	exit(0);
	}
	std::string jobid(argv[1]);
	char * user_char = getlogin();
	std::string user(user_char);
	std::string command = default_directory + "gorque.py -u " + user + " -d " + jobid;
	// std::cout << command;
	setuid(0);
	system(command.c_str());
	return 0;
}