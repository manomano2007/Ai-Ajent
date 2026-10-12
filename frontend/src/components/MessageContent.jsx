import { useState } from "react";
import { CheckIcon, CopyIcon } from "./icons.jsx";

function splitIntoBlocks(text) {
  const blocks = [];
  const parts = text.split("```");

  parts.forEach((part, index) => {
    const isCode = index % 2 === 1;

    if (!isCode) {
      if (part.trim()) {
        blocks.push({ type: "text", content: part.trim() });
      }
      return;
    }

    const newlineIndex = part.indexOf("\n");
    let language = "";
    let code = part;

    if (newlineIndex !== -1) {
      language = part.slice(0, newlineIndex).trim();
      code = part.slice(newlineIndex + 1);
    }

    blocks.push({ type: "code", language, content: code.replace(/\n$/, "") });
  });

  return blocks;
}

// Splits text into inline pieces. Odd indexes are the matched **bold** or `code` parts.
function renderInline(text) {
  const parts = text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g);

  return parts.map((part, index) => {
    if (!part) return null;

    if (index % 2 === 1) {
      if (part.startsWith("**")) {
        return <strong key={index}>{part.slice(2, -2)}</strong>;
      }
      return <code key={index}>{part.slice(1, -1)}</code>;
    }

    return <span key={index}>{part}</span>;
  });
}

// Turns plain text into headings, lists, and paragraphs.
function parseMarkdownBlocks(text) {
  const nodes = [];
  let paragraph = [];
  let list = null;

  const flushParagraph = () => {
    if (paragraph.length) {
      nodes.push({ type: "p", text: paragraph.join("\n") });
      paragraph = [];
    }
  };

  const flushList = () => {
    if (list) {
      nodes.push(list);
      list = null;
    }
  };

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trimEnd();

    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    if (heading) {
      flushParagraph();
      flushList();
      nodes.push({ type: "heading", level: heading[1].length, text: heading[2] });
      continue;
    }

    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    if (bullet) {
      flushParagraph();
      if (!list || list.type !== "ul") {
        flushList();
        list = { type: "ul", items: [] };
      }
      list.items.push(bullet[1]);
      continue;
    }

    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (numbered) {
      flushParagraph();
      if (!list || list.type !== "ol") {
        flushList();
        list = { type: "ol", items: [] };
      }
      list.items.push(numbered[1]);
      continue;
    }

    flushList();
    paragraph.push(line.trim());
  }

  flushParagraph();
  flushList();
  return nodes;
}

function renderTextBlock(text) {
  return parseMarkdownBlocks(text).map((node, index) => {
    if (node.type === "heading") {
      const Tag = node.level === 1 ? "h3" : node.level === 2 ? "h4" : "h5";
      return (
        <Tag key={index} className="md-heading">
          {renderInline(node.text)}
        </Tag>
      );
    }

    if (node.type === "ul") {
      return (
        <ul key={index} className="md-list">
          {node.items.map((item, i) => (
            <li key={i}>{renderInline(item)}</li>
          ))}
        </ul>
      );
    }

    if (node.type === "ol") {
      return (
        <ol key={index} className="md-list">
          {node.items.map((item, i) => (
            <li key={i}>{renderInline(item)}</li>
          ))}
        </ol>
      );
    }

    return (
      <p key={index} className="md-paragraph">
        {renderInline(node.text)}
      </p>
    );
  });
}

function CodeBlock({ code, language }) {
  const [status, setStatus] = useState("idle");

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(code);
      setStatus("copied");
    } catch {
      setStatus("failed");
    }
    setTimeout(() => setStatus("idle"), 1800);
  }

  const label =
    status === "copied" ? "Copied" : status === "failed" ? "Copy failed" : "Copy";

  return (
    <div className="code-block">
      <div className="code-header">
        <span className="code-language">{language || "code"}</span>
        <button
          type="button"
          className={`copy-button ${status}`}
          onClick={copyCode}
          aria-label={`Copy ${language || "code"} to clipboard`}
        >
          {status === "copied" ? (
            <CheckIcon width={14} height={14} />
          ) : (
            <CopyIcon width={14} height={14} />
          )}
          <span>{label}</span>
        </button>
      </div>
      <pre className="code-pre">
        <code>{code}</code>
      </pre>
    </div>
  );
}

export default function MessageContent({ text }) {
  const blocks = splitIntoBlocks(text);

  return (
    <div className="message-content">
      {blocks.map((block, index) =>
        block.type === "code" ? (
          <CodeBlock key={index} code={block.content} language={block.language} />
        ) : (
          <div key={index} className="md-text">
            {renderTextBlock(block.content)}
          </div>
        )
      )}
    </div>
  );
}