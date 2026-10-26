"use client";
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { paginateText, pageForOffset, type ReadingPage } from "./pagination";
import "./reading.css";

type Props = { text: string; storageKey?: string; readingKey?: string; streaming?: boolean; initialOffset?: number; onOffsetChange?: (offset: number) => void; className?: string; onNextBoundary?: () => void; onPreviousBoundary?: () => void; nextBoundaryDisabled?: boolean; previousBoundaryDisabled?: boolean; controlsExtra?: ReactNode; narrative?: boolean; scrollable?: boolean };
export function PagedReading({ text, storageKey, readingKey, streaming, initialOffset = 0, onOffsetChange, className = "", onNextBoundary, onPreviousBoundary, nextBoundaryDisabled, previousBoundaryDisabled, controlsExtra, narrative, scrollable = false }: Props) {
  const viewport = useRef<HTMLDivElement>(null);
  const measure = useRef<HTMLDivElement>(null);
  const offset = useRef(initialOffset);
  const previousReading = useRef({ key: readingKey, text, streaming });
  const [pages, setPages] = useState<ReadingPage[]>([{ start: 0, end: text.length, text }]);
  const [index, setIndex] = useState(0);
  useLayoutEffect(() => {
    offset.current = initialOffset;
    if (storageKey) { try { const value = localStorage.getItem(storageKey); const saved = Number(value); if (value !== null && Number.isFinite(saved)) offset.current = Math.max(0, saved); } catch { /* Reading works without storage. */ } }
  }, [storageKey, initialOffset]);
  useLayoutEffect(() => {
    const previous = previousReading.current;
    if (readingKey !== previous.key) {
      const continuation = previous.streaming && previous.text ? text.indexOf(previous.text) : -1;
      offset.current = continuation >= 0 ? offset.current + continuation : initialOffset;
    }
    previousReading.current = { key: readingKey, text, streaming };
  }, [readingKey, text, streaming, initialOffset]);
  useLayoutEffect(() => {
    const update = () => {
      if (!viewport.current || !measure.current) return;
      const element = measure.current;
      element.style.width = `${viewport.current.clientWidth}px`;
      const height = Math.max(1, viewport.current.clientHeight);
      const next = paginateText(text, candidate => { element.textContent = candidate; return element.scrollHeight <= height; });
      element.textContent = "";
      setPages(next);
      setIndex(pageForOffset(next, offset.current));
    };
    update();
    const observer = new ResizeObserver(update);
    if (viewport.current) observer.observe(viewport.current);
    let disposed = false;
    void document.fonts.ready.then(() => { if (!disposed) update(); });
    return () => { disposed = true; observer.disconnect(); };
  }, [text, storageKey, readingKey, initialOffset]);
  const turn = (next: number) => {
    if (next < 0) { onPreviousBoundary?.(); return; }
    if (next >= pages.length) { onNextBoundary?.(); return; }
    offset.current = pages[next].start;
    setIndex(next);
    if (viewport.current) viewport.current.scrollTop = 0;
    if (storageKey) { try { localStorage.setItem(storageKey, String(offset.current)); } catch { /* Optional persistence. */ } }
    onOffsetChange?.(offset.current);
  };
  const atFirstPage = index === 0;
  const atLastPage = index === pages.length - 1;
  const previousDisabled = atFirstPage && (!onPreviousBoundary || previousBoundaryDisabled);
  const nextDisabled = atLastPage && (!onNextBoundary || nextBoundaryDisabled);
  const previousLabel = narrative && atFirstPage && !previousDisabled ? "上一段" : "上一页";
  const nextLabel = narrative && atLastPage && !nextDisabled ? "下一段" : "下一页";
  const showPrevious = pages.length > 1 || Boolean(onPreviousBoundary);
  const showNext = pages.length > 1 || Boolean(onNextBoundary);
  const showControls = showPrevious || showNext || Boolean(controlsExtra);
  if (scrollable) {
    return <div className={`paged-reading ${className} scrollable-reading`} data-reading-offset={0}>
      <div className="reading-viewport scroll-mode" tabIndex={0} aria-label="正文"><div className="reading-text">{text}</div></div>
      <div className="reading-measure reading-text" ref={measure} aria-hidden="true" />
      {showControls && <nav className="reading-controls" aria-label="正文翻页">
        {showPrevious && <button type="button" aria-label={previousLabel} disabled={previousDisabled} onClick={() => turn(index - 1)}>{previousLabel}</button>}
        {showNext && <button type="button" aria-label={nextLabel} disabled={nextDisabled} onClick={() => turn(index + 1)}>{nextLabel}</button>}
        {controlsExtra}
      </nav>}
    </div>;
  }
  return <div className={`paged-reading ${className}`} data-reading-offset={pages[index]?.start || 0}>
    <div className="reading-viewport" ref={viewport} tabIndex={0} aria-label="分页正文" aria-live="polite" onKeyDown={event => {
      if (["ArrowRight", "PageDown"].includes(event.key)) {
        event.preventDefault();
        turn(index + 1);
      } else if (["ArrowLeft", "PageUp"].includes(event.key)) {
        event.preventDefault();
        turn(index - 1);
      }
    }}><div className="reading-text" key={`${readingKey || storageKey || "reading"}:${index}`}>{pages[index]?.text}</div></div>
    <div className="reading-measure reading-text" ref={measure} aria-hidden="true" />
    {showControls && <nav className="reading-controls" data-tutorial-id={narrative ? "narrative-controls" : undefined} aria-label={narrative ? "剧情阅读控制" : "正文翻页"}>
      {showPrevious && <button type="button" aria-label={previousLabel} disabled={previousDisabled} onClick={() => turn(index - 1)}>{previousLabel}</button>}
      {showNext && <button type="button" aria-label={nextLabel} disabled={nextDisabled} onClick={() => turn(index + 1)}>{nextLabel}</button>}
      {controlsExtra}
    </nav>}
  </div>;
}
