# external

teleport项目用到的第三方库

- openssl
  https://www.openssl.org
  openssl-1.0.2p
  请按openssl文档所述，编译出openssl的静态库。要编译openssl，需要
  - perl 建议安装ActivePerl http://www.activestate.com/ActivePerl
  - nasm http://www.nasm.us


- jsoncpp
  https://github.com/open-source-parsers/jsoncpp
  jsoncpp 0.10.6
  注意：之所以不使用新的1.x.y版本，是因为1.x.y版本需要编译器支持C++11，而为了Linux平台的兼容性，使用的低版本GCC和libc++库，并不支持C++11。
  注意：teleport项目使用源代码直接编译，因此解压缩源代码到此即可。
- mongoose
  https://github.com/cesanta/mongoose
  mongoose 6.12
  注意：teleport项目使用源代码直接编译，因此解压缩源代码到此即可。
- sqlite3
  http://sqlite.org/download.html
  sqlite3-autoconf-3250000
  注意：teleport项目使用源代码直接编译，因此解压缩源代码到此即可。
- mbedtls
  https://github.com/ARMmbed/mbedtls
  mbedtls-mbedtls-2.12.0
  注意：teleport项目使用源代码直接编译，因此解压缩源代码到此即可。
- libssh
  https://git.libssh.org/projects/libssh.git/snapshot
  libssh-0.8.5.zip
  Windows平台使用预制的libssh-static工程进行编译。
- libuv
  https://github.com/libuv/libuv
  v1.23.0.zip
  注意：teleport项目使用源代码直接编译，因此解压缩源代码到此即可。






