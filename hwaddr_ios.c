#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>
#include <sys/errno.h>
#include <net/if.h>
#include <net/if_dl.h>
#include <net/ethernet.h>
#include <sys/types.h>
#include <sys/sysctl.h>

int main(int argc, char *argv[])
{

	if(argc < 2)
	{
		printf("usage %s [devicename]",argv[1]);
		return 0;
	}
	int mib[6], len;

	mib[0] = CTL_NET;
	mib[1] = AF_ROUTE;
	mib[2] = 0;
	mib[3] = AF_LINK;
	mib[4] = NET_RT_IFLIST;
	mib[5] = if_nametoindex(argv[1]);

	if (mib[5] == 0)
	{
		printf("error calling if_nametoindex(%s)\n",argv[1]);
		return -1;
	}

	if (sysctl(mib, 6, NULL, (size_t*)&len, NULL, 0) < 0)
	{
		printf("sysctl 1 error\n");
		return -1;
	}

	char * macbuf = (char*) malloc(len);
	if (sysctl(mib, 6, macbuf, (size_t*)&len, NULL, 0) < 0)
	{
		printf("sysctl 2 error");
		return -1;
	}

	struct if_msghdr * ifm = (struct if_msghdr *)macbuf;
	struct sockaddr_dl * sdl = (struct sockaddr_dl *)(ifm + 1);
	unsigned char * ptr = (unsigned char *)LLADDR(sdl);
	printf("MacAddress: %02x:%02x:%02x:%02x:%02x:%02x\n", *ptr,
			*(ptr+1), *(ptr+2),
			*(ptr+3), *(ptr+4), *(ptr+5));

	free(macbuf);

	return 0;
}
