import base64

# フォルダ名のマッピング: 現在の名前 -> 移動先の科目名
mappings = [
    ("\u5927\u5b66\u7ba1\u7406\u4f1a\u8a08", "\u7ba1\u7406\u4f1a\u8a08"),
    ("\u5927\u5b66\u751f\u7523\u30fb\u6d41\u901a\u30de\u30cd\u30b8\u30e1\u30f3\u30c8", "\u751f\u7523\u30fb\u6d41\u901a\u30de\u30cd\u30b8\u30e1\u30f3\u30c8"),
    ("\u5927\u5b66\u88fd\u54c1\u958b\u767a\u5de5\u5b66", "\u88fd\u54c1\u958b\u767a\u5de5\u5b66"),
    ("\u5927\u5b66\u529b\u5b66C", "\u529b\u5b66C"),
    ("\u5927\u5b66\u30a4\u30ce\u30d9\u30fc\u30b7\u30e7\u30f3\u3068\u30aa\u30da\u30ec\u30fc\u30b7\u30e7\u30f3\u30ba\u306e\u30de\u30cd\u30b8\u30e1\u30f3\u30c8", "\u30a4\u30ce\u30d9\u30fc\u30b7\u30e7\u30f3\u3068\u30aa\u30da\u30ec\u30fc\u30b7\u30e7\u30f3\u30ba\u306e\u30de\u30cd\u30b8\u30e1\u30f3\u30c8"),
    ("\u5927\u5b66\u751f\u7523\u30b7\u30b9\u30c6\u30e0\u8ad6\u3068\u9032\u5316\u578b\u8a08\u7b97", "\u751f\u7523\u30b7\u30b9\u30c6\u30e0\u8ad6\u3068\u9032\u5316\u578b\u8a08\u7b97"),
    ("\u5927\u5b66\u5316\u5b66\u71b1\u529b\u5b66", "\u5316\u5b66\u71b1\u529b\u5b66"),
    ("\u5927\u5b66\u5fdc\u7528\u30b7\u30b9\u30c6\u30e0\u601d\u8003", "\u5fdc\u7528\u30b7\u30b9\u30c6\u30e0\u601d\u8003"),
    ("\u5927\u5b66\u591a\u5909\u91cf\u89e3\u6790\u6cd5", "\u591a\u5909\u91cf\u89e3\u6790\u6cd5"),
    ("\u5927\u5b66\u6750\u6599\u529b\u5b66B", "\u6750\u6599\u529b\u5b66B"),
    ("\u5927\u5b66\u56fd\u969b\u5354\u529b\u8ad6", "\u56fd\u969b\u5354\u529b\u8ad6"),
    ("\u5927\u5b66\u7cbe\u795e\u5206\u6790\u8ad6", "\u7cbe\u795e\u5206\u6790\u8ad6"),
    ("\u5927\u5b66\u5171\u5275\u30ef\u30fc\u30af\u30b7\u30e7\u30c3\u30d7\u6f14\u7fd2", "\u5171\u5275\u30ef\u30fc\u30af\u30b7\u30e7\u30c3\u30d7\u6f14\u7fd2"),
]

lines = [
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8",
    "$OD  = 'C:\\Users\\kazuy\\OneDrive'",
    "$UNI = 'C:\\Users\\kazuy\\OneDrive\\\u5927\u5b66'",
    "",
]

for src_name, dst_name in mappings:
    lines.append(f"$src = \"$OD\\{src_name}\"")
    lines.append(f"$dst = \"$UNI\\{dst_name}\"")
    lines.append("if (Test-Path $src) {")
    lines.append(f"    Move-Item -LiteralPath $src -Destination $dst -Force")
    lines.append(f"    Write-Host \"\u79fb\u52d5: {src_name} -> {dst_name}\"")
    lines.append("} else {")
    lines.append(f"    Write-Host \"\u306a\u3057: {src_name}\"")
    lines.append("}")

lines.append("Write-Host \"\u5b8c\u4e86\"")

script = "\n".join(lines)
encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
print(encoded)
