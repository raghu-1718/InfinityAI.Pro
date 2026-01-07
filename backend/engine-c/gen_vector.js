const crypto = require('crypto');

const KEY_HEX = "758c6bfc504fbffce67090816617dbfb6556770c3e5105fe40b7f69a37d4f5ee";
const PLAINTEXT = "TopSecret123";
const ALGORITHM = "aes-256-gcm";

function encrypt() {
    const iv = crypto.randomBytes(12);
    const key = Buffer.from(KEY_HEX, "hex");
    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
    
    let encrypted = cipher.update(PLAINTEXT, "utf8", "hex");
    encrypted += cipher.final("hex");
    
    const authTag = cipher.getAuthTag().toString("hex");
    
    // Format: iv:authTag:encrypted
    const result = `${iv.toString("hex")}:${authTag}:${encrypted}`;
    
    console.log("KEY_HEX:", KEY_HEX);
    console.log("PLAINTEXT:", PLAINTEXT);
    console.log("FULL_CIPHERTEXT:", result);
}

encrypt();
