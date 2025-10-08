import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Copy, Check } from 'lucide-react';
import 'katex/dist/katex.min.css';

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const copyToClipboard = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className="prose prose-invert max-w-none text-[0.9375rem] leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code({ node, className, children, ...props }: any) {
            const isInline = !className;
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');
            const codeId = `code-${Math.random().toString(36).substr(2, 9)}`;

            if (!isInline && match) {
              return (
                <div className="my-4 rounded-lg overflow-hidden border border-[#30363d] bg-[#0d1117]">
                  <div className="flex items-center justify-between px-4 py-2 bg-[#161b22] border-b border-[#30363d]">
                    <span className="text-xs font-mono font-semibold text-green-400 tracking-wide">{match[1]}</span>
                    <button
                      onClick={() => copyToClipboard(codeString, codeId)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-300 hover:text-white bg-[#21262d] hover:bg-green-500 rounded-lg transition-all"
                      title="Copy code"
                    >
                      {copiedCode === codeId ? (
                        <>
                          <Check size={14} />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy size={14} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    showLineNumbers={true}
                    customStyle={{
                      margin: 0,
                      borderRadius: 0,
                      fontSize: '0.875rem',
                      background: '#0d1117',
                      padding: '1rem',
                    }}
                    lineNumberStyle={{
                      minWidth: '3em',
                      paddingRight: '1em',
                      color: '#6e7681',
                      userSelect: 'none',
                    }}
                  >
                    {codeString}
                  </SyntaxHighlighter>
                </div>
              );
            }

            return (
              <code className="bg-[#2a2a2a] px-1.5 py-0.5 rounded text-sm text-green-500 font-mono" {...props}>
                {children}
              </code>
            );
          },
          a({ children, href, ...props }: any) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-green-500 no-underline border-b border-transparent hover:border-green-500 transition-all"
                {...props}
              >
                {children}
              </a>
            );
          },
          table({ children, ...props }: any) {
            return (
              <div className="overflow-x-auto my-4">
                <table className="w-full border-collapse text-sm" {...props}>{children}</table>
              </div>
            );
          },
          thead({ children, ...props }: any) {
            return (
              <thead className="border-b border-white/10" {...props}>{children}</thead>
            );
          },
          th({ children, ...props }: any) {
            return (
              <th className="px-3 py-3 text-left bg-[#1a2a1a] font-semibold text-green-500" {...props}>{children}</th>
            );
          },
          td({ children, ...props }: any) {
            return (
              <td className="px-3 py-3 border border-[#2a2a2a] bg-[#1a1a1a]" {...props}>{children}</td>
            );
          },
          tr({ children, ...props }: any) {
            return (
              <tr className="hover:bg-[#222] transition-colors" {...props}>{children}</tr>
            );
          },
          blockquote({ children, ...props }: any) {
            return (
              <blockquote className="my-4 py-3 px-4 border-l-4 border-green-500 bg-[#1a2a1a] text-gray-300" {...props}>{children}</blockquote>
            );
          },
          ul({ children, ...props }: any) {
            return (
              <ul className="my-4 pl-6 list-disc" {...props}>{children}</ul>
            );
          },
          ol({ children, ...props }: any) {
            return (
              <ol className="my-4 pl-6 list-decimal" {...props}>{children}</ol>
            );
          },
          li({ children, ...props }: any) {
            return (
              <li className="my-1" {...props}>{children}</li>
            );
          },
          p({ children, ...props }: any) {
            return (
              <p className="my-4 last:mb-0" {...props}>{children}</p>
            );
          },
          h1({ children, ...props }: any) {
            return (
              <h1 className="mt-6 mb-3 text-3xl font-semibold text-white first:mt-0" {...props}>{children}</h1>
            );
          },
          h2({ children, ...props }: any) {
            return (
              <h2 className="mt-6 mb-3 text-2xl font-semibold text-white first:mt-0" {...props}>{children}</h2>
            );
          },
          h3({ children, ...props }: any) {
            return (
              <h3 className="mt-6 mb-3 text-xl font-semibold text-white first:mt-0" {...props}>{children}</h3>
            );
          },
          h4({ children, ...props }: any) {
            return (
              <h4 className="mt-6 mb-3 text-lg font-semibold text-white first:mt-0" {...props}>{children}</h4>
            );
          },
          pre({ children }: any) {
            return <>{children}</>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
