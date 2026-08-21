const fs = require('fs');
const path = require('path');

// Dynamically check and output if dependencies are missing
try {
  const parser = require('@babel/parser');
  const traverse = require('@babel/traverse').default;
  const generator = require('@babel/generator').default;

  const filePath = process.argv[2];
  const line = parseInt(process.argv[3], 10);
  const col = parseInt(process.argv[4], 10);
  const replacement = process.argv[5];

  const code = fs.readFileSync(filePath, 'utf-8');

  // Parse TS/JS source code
  const ast = parser.parse(code, {
    sourceType: 'module',
    plugins: ['typescript', 'jsx']
  });

  let patched = false;

  traverse(ast, {
    CallExpression(astPath) {
      const loc = astPath.node.loc;
      if (loc && loc.start.line === line) {
        const colStart = loc.start.column;
        const colEnd = loc.end.column;

        // Check if column matches or is within bounds
        if (isNaN(col) || (col >= colStart && col <= colEnd)) {
          // Parse replacement locator code into AST node
          const replacementAst = parser.parse(replacement, { sourceType: 'script' }).program.body[0].expression;
          astPath.replaceWith(replacementAst);
          patched = true;
          astPath.stop();
        }
      }
    }
  });

  if (patched) {
    const output = generator(ast, { retainLines: true }, code);
    fs.writeFileSync(filePath, output.code, 'utf-8');
    console.log("SUCCESS: Patched TypeScript AST.");
    process.exit(0);
  } else {
    console.error("ERROR: No matching CallExpression found at coordinates.");
    process.exit(1);
  }
} catch (err) {
  console.error("BABEL_MISSING: " + err.message);
  process.exit(2);
}
