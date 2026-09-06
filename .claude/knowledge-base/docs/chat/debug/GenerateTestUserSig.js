/*eslint-disable*/

/**
 * ⚠️ 仅用于本地开发调试！
 * 上线前必须：
 *   1. 删除整个 public/debug/ 目录
 *   2. 从 index.html 移除两行 <script> 引入
 *   3. 改为调用后端签发接口获取 UserSig
 * 后端签发文档：https://cloud.tencent.com/document/product/269/32688
 */

const SDKAPPID = 0;
const SECRETKEY = '';
const EXPIRETIME = 604800; // 默认时间：7 x 24 x 60 x 60 = 604800 = 7 天，时间单位：秒

function genTestUserSig(userID) {
  const generator = new window.LibGenerateTestUserSig(SDKAPPID, SECRETKEY, EXPIRETIME);
  const userSig = generator.genTestUserSig(userID);
  return {
    SDKAppID: SDKAPPID,
    userSig: userSig
  };
}
