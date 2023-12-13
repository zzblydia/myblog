#include <openssl/hmac.h>

int main() {
    HMAC_CTX* ctx;
	ctx = HMAC_CTX_new();
    return 0;
}