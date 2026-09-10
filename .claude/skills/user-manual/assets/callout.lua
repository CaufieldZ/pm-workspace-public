-- callout.lua — pandoc Lua filter（user-manual skill）
-- 把以 【…】（含【⚠️ 风险提示】）或裸 ⚠️ 开头的 blockquote 转成 docx 的 Callout 段落样式
-- （底纹 + 左色条，样式定义在 assets/user-manual-reference.docx）。
-- 不匹配标记的普通 blockquote 不动，保持 pandoc 默认 Quote 渲染。
-- help-center md 不经此 filter，callout 仍是标准 blockquote。

local MARKERS = { "【", "⚠️", "⚠" }

-- 取 blockquote 第一段的纯文本前缀，判断是否 callout
local function leading_text(blocks)
  if not blocks[1] then return "" end
  local first = blocks[1]
  if first.t == "Para" or first.t == "Plain" then
    return pandoc.utils.stringify(first):gsub("^%s+", "")
  end
  return ""
end

local function is_callout(blocks)
  local txt = leading_text(blocks)
  for _, m in ipairs(MARKERS) do
    if txt:sub(1, #m) == m then return true end
  end
  return false
end

function BlockQuote(el)
  if not is_callout(el.content) then
    return nil -- 非 callout，原样
  end
  -- 包成带 custom-style 的 Div → pandoc docx 套用 reference.docx 的 "Callout" 段落样式
  return pandoc.Div(el.content, pandoc.Attr("", {}, { ["custom-style"] = "Callout" }))
end
