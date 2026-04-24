import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist/legacy/build/pdf'
// Vite-friendly worker bundling
// eslint-disable-next-line import/no-unresolved
import pdfWorker from 'pdfjs-dist/legacy/build/pdf.worker?url'

GlobalWorkerOptions.workerSrc = pdfWorker

async function readTxt(file: File): Promise<string> {
  return await file.text()
}

async function readPdf(file: File): Promise<string> {
  const buf = await file.arrayBuffer()
  const pdf = await getDocument({ data: buf }).promise

  const pages: string[] = []
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i)
    const content = await page.getTextContent()
    const text = content.items
      // pdf.js text items can be different shapes; this is the safe path.
      .map((it) => ('str' in it ? String(it.str) : ''))
      .join(' ')
      .replace(/\s+/g, ' ')
      .trim()
    if (text) pages.push(text)
  }

  return pages.join('\n\n')
}

export async function fileToText(file: File): Promise<{ text: string; kind: 'txt' | 'pdf' | 'unknown' }> {
  const name = file.name.toLowerCase()
  if (file.type === 'text/plain' || name.endsWith('.txt')) {
    return { text: await readTxt(file), kind: 'txt' }
  }
  if (file.type === 'application/pdf' || name.endsWith('.pdf')) {
    return { text: await readPdf(file), kind: 'pdf' }
  }
  return { text: await readTxt(file), kind: 'unknown' }
}

