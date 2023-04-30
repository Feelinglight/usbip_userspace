#ifndef __SSL_UTILS_H
#define __SSL_UTILS_H

#include <openssl/bio.h>
#include <openssl/ssl.h>
#include <openssl/err.h>


void init_libssl();
void deinit_libssl();
void destroy_connection(SSL *ssl_conn);
SSL* wrap_connection(int sockfd);

#endif // __SSL_UTILS_H
