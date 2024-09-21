CC = gcc
CFLAGS = -fPIC -Wall -I.
OUTPUT = libfileops.so
SRC = fileops.c utils.c
HEADERS = fileops.h utils.h

# Target for shared object
$(OUTPUT): $(SRC) $(HEADERS)
	$(CC) $(CFLAGS) -shared -o $(OUTPUT) $(SRC)

clean:
	rm -f $(OUTPUT)
	rm -f *.o

