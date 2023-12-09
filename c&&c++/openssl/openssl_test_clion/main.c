#include <openssl/hmac.h>

int main() {
    HMAC_CTX* ctx;
    unsigned char key[] = "mykey";
    unsigned char data[] = "Hello, world!";
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int digest_len;

    // 创建 HMAC 上下文对象
    ctx = HMAC_CTX_new();
    if (ctx == NULL) {
        // 处理上下文创建失败的情况
        // ...
        return 1;
    }

    // 初始化 HMAC 上下文
    HMAC_Init_ex(ctx, key, sizeof(key) - 1, EVP_sha256(), NULL);

    // 更新数据
    HMAC_Update(ctx, data, sizeof(data) - 1);

    // 计算 HMAC 值
    HMAC_Final(ctx, digest, &digest_len);

    // 打印 HMAC 值
    for (int i = 0; i < digest_len; i++) {
        printf("%02x", digest[i]);
    }
    printf("\n");

    // 清理并释放上下文对象
    HMAC_CTX_free(ctx);

    return 0;
}