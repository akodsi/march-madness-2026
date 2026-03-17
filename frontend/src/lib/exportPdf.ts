import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

/**
 * Capture a DOM element as a PDF and trigger download.
 * Uses landscape letter size to fit bracket layout.
 */
export async function exportBracketPdf(element: HTMLElement, filename = 'bracket-2026.pdf') {
  // Capture at 2x for crisp output
  const canvas = await html2canvas(element, {
    backgroundColor: '#0f172a', // slate-900
    scale: 2,
    useCORS: true,
    logging: false,
  })

  const imgData = canvas.toDataURL('image/png')
  const imgW = canvas.width
  const imgH = canvas.height

  // Landscape letter: 11 × 8.5 inches → 792 × 612 points
  const pdf = new jsPDF({
    orientation: 'landscape',
    unit: 'pt',
    format: 'letter',
  })

  const pageW = pdf.internal.pageSize.getWidth()
  const pageH = pdf.internal.pageSize.getHeight()
  const margin = 20

  const availW = pageW - margin * 2
  const availH = pageH - margin * 2

  // Scale image to fit within the page
  const scale = Math.min(availW / imgW, availH / imgH)
  const drawW = imgW * scale
  const drawH = imgH * scale

  // Center on page
  const x = margin + (availW - drawW) / 2
  const y = margin + (availH - drawH) / 2

  pdf.addImage(imgData, 'PNG', x, y, drawW, drawH)
  pdf.save(filename)
}
