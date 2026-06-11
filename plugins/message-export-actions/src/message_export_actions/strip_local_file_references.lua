local function is_remote_uri(target)
  return target:match("^[a-zA-Z][a-zA-Z0-9+.-]*:") and not target:match("^file:")
end

function Link(el)
  local target = el.target or ""

  if target == "" then
    return el
  end

  if target:match("^#") then
    return el
  end

  if is_remote_uri(target) then
    return el
  end

  local text = pandoc.utils.stringify(el.content)
  if text == nil or text == "" then
    text = target
  end

  return pandoc.Str(text)
end