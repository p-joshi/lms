import { Fragment, createElement } from 'preact';

import Table from './Table';

/**
 * @typedef {import('../api-types').Chapter} Chapter
 */

/**
 * @typedef ChapterListProps
 * @prop {Chapter[]} chapters - List of available chapters
 * @prop {boolean} [isLoading] - Whether to show a loading indicator
 * @prop {Chapter|null} selectedChapter - The chapter within `chapters` which is currently selected
 * @prop {(c: Chapter) => any} [onSelectChapter] -
 *   Callback invoked when the user clicks on a chapter
 * @prop {(c: Chapter) => any} [onUseChapter] -
 *   Callback invoked when the user double-clicks a chapter
 */

/**
 * @param {ChapterListProps} props
 */
export default function ChapterList({
  chapters,
  isLoading = false,
  selectedChapter,
  onSelectChapter,
  onUseChapter,
}) {
  const columns = [
    {
      label: 'Title',
    },
    {
      label: 'Page',
    },
  ];

  return (
    <Table
      accessibleLabel="Table of Contents"
      columns={columns}
      contentLoading={isLoading}
      items={chapters}
      onSelectItem={onSelectChapter}
      onUseItem={onUseChapter}
      selectedItem={selectedChapter}
      renderItem={chapter => (
        <Fragment>
          <td aria-label={chapter.title}>{chapter.title}</td>
          <td>{chapter.page}</td>
        </Fragment>
      )}
    />
  );
}
