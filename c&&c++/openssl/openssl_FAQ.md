# some usages

## compile error

### openssl-1.1.1m
```
./config --prefix=/opt/openssl --openssldir=/opt/openssl -d
```
```
/usr/bin/ld: crypto/bn/x86_64-mont.o: relocation R_X86_64_PC32 against undefined symbol `bn_sqrx8x_internal' can not be used when making a shared object; recompile with -fPIC
```
```
/opt/packages/openssl-1.1.1m/crypto/bn/x86_64-mont.s:781: undefined reference to `bn_sqrx8x_internal'
```

## command
```
openssl req -new -newkey rsa:2048 -days 10000 -nodes -x509 -subj "/O=lws/CN=1.2.3.4" -keyout "libwebsockets-test-server.key.pem" -out "libwebsockets-test-server.pem" -extensions SAN -config <(echo "[req]"; echo distinguished_name=req; echo "[SAN]"; echo subjectAltName=IP:1.2.3.4)
```

```
openssl x509 -in libwebsockets-test-server.pem -text -noout
```
