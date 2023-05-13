#ifndef __SSL_UTILS_H
#define __SSL_UTILS_H

#include <openssl/bio.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

enum ssl_side {
    ssl_client,
    ssl_server
};

void init_libssl(enum ssl_side);
void deinit_libssl();

SSL* wrap_server_connection(int sockfd);
void destroy_connection(SSL *ssl_conn);

SSL* ssl_client_init(int sockfd);

#endif // __SSL_UTILS_H
