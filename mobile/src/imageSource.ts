import { API_URL, media } from './api';
import { catalogImages } from './catalogImages';

export function imageSource(src: string): { source: number | { uri: string }; placeholder?: string } {
  // Only substitute our bundled catalog URLs, never a third-party file with the same name.
  const origin = API_URL.replace(/\/api\/v1$/, '');
  const path = src.startsWith(origin + '/') ? src.slice(origin.length) : src;
  const bundled = catalogImages[path];
  return { source: bundled?.source ?? { uri: media(src) }, placeholder: bundled?.placeholder };
}
