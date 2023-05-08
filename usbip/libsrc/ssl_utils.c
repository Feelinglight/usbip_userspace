#include "ssl_utils.h"
#include <openssl/pem.h>
#include "usbip_common.h"


static SSL_CTX *ssl_context;

void init_libssl(enum ssl_side side)
{
    SSL_load_error_strings();
    SSL_library_init();
    OpenSSL_add_all_algorithms();

    if (side == ssl_server) {
        ssl_context = SSL_CTX_new(SSLv23_server_method());
    } else {
        ssl_context = SSL_CTX_new(SSLv23_client_method());
    }
    SSL_CTX_set_options(ssl_context, SSL_OP_SINGLE_DH_USE);
}

void deinit_libssl()
{
    ERR_free_strings();
    EVP_cleanup();
}

SSL* wrap_server_connection(int sockfd)
{
    int ssl_err;
    SSL *ssl_conn;
    int use_cert;
    int use_key;

    use_cert = SSL_CTX_use_certificate_file(
        ssl_context, "/etc/ssl/certs/usbip.pem" , SSL_FILETYPE_PEM);
    use_key = SSL_CTX_use_PrivateKey_file(
        ssl_context, "/etc/ssl/private/usbip.key", SSL_FILETYPE_PEM);

    if (!use_cert || !use_key) {
        err("Cant use ca files, use_cert: %d, use_key: %d", use_cert, use_key);
        return NULL;
    }
    ssl_conn = SSL_new(ssl_context);
    SSL_set_fd(ssl_conn, sockfd);

    ssl_err = SSL_accept(ssl_conn);
    if(ssl_err <= 0) {
        err("SSL_accept error, err code: %d", ssl_err);
        destroy_connection(ssl_conn);
        return NULL;
    }
    return ssl_conn;
}

void destroy_connection(SSL *ssl_conn)
{
    SSL_shutdown(ssl_conn);
    SSL_free(ssl_conn);
}

SSL* ssl_client_init(int sockfd)
{
    SSL* ssl_conn = SSL_new(ssl_context);
    SSL_set_fd(ssl_conn, sockfd);

    return ssl_conn;
}
