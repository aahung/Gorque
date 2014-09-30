CC=g++
CFLAGS= 
GSUBSRC= gosub.cpp
GSTSRC= gostat.cpp
GDSRC= godaemon.cpp
GDELSRC= godel.cpp
OUTPUTDIR= production
GSUBEXEC= gosub
GSTEXEC= gostat
GDEXEC= godaemon
GDELEXEC= godel

all: gosub gostat godaemon python godel

gostat:
		$(CC) -o $(OUTPUTDIR)/$(GSTEXEC) $(GSTSRC) $(CFLAGS)

gosub:
		$(CC) -o $(OUTPUTDIR)/$(GSUBEXEC) $(GSUBSRC) $(CFLAGS)

godaemon:
		$(CC) -o $(OUTPUTDIR)/$(GDEXEC) $(GDSRC) $(CFLAGS)

godel:
		$(CC) -o $(OUTPUTDIR)/$(GDELEXEC) $(GDELSRC) $(CFLAGS)

python:
		cp gorque.py $(OUTPUTDIR)/gorque.py


clean:
		rm *.o *.linkinfo