/* This file is auto-generated, please do not edit it manually */

importScripts('https://storage.googleapis.com/workbox-cdn/releases/4.3.1/workbox-sw.js');

const MINUTE = 60; // seconds
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const WEEK = 7 * DAY;

// https://developers.google.com/web/tools/workbox/modules/workbox-core#skip_waiting_and_clients_claim
workbox.core.skipWaiting();
workbox.core.clientsClaim();

// https://developers.google.com/web/tools/workbox/modules/workbox-precaching#reading_precached_assets_directly
workbox.precaching.cleanupOutdatedCaches();

// https://developers.google.com/web/tools/workbox/modules/workbox-precaching#serving_precached_responses
workbox.precaching.precacheAndRoute([
  {
    "url": "index.html",
    "revision": "c1f245e1cc42f5e9fe41bee0ab1c68b4"
  },
  {
    "url": "static/css/accession.39bbe650.chunk.css",
    "revision": "0056ca5d583bccde6a76b647a6b6b330"
  },
  {
    "url": "static/css/advanced-search.2edb7cbb.chunk.css",
    "revision": "abbee3a18abdf32bd3875116da55ae09"
  },
  {
    "url": "static/css/browse.f8561778.chunk.css",
    "revision": "e0babe0e6069c46ae9faa80867493c46"
  },
  {
    "url": "static/css/contact.8876a84b.chunk.css",
    "revision": "e70580a2561c1b56ccea8a387d390354"
  },
  {
    "url": "static/css/custom-search.06422cd3.chunk.css",
    "revision": "de024a87eef1b647b2bcbbceea42e0d2"
  },
  {
    "url": "static/css/dist-perres.67b1e5d3.chunk.css",
    "revision": "51858d9a9954e8d0902f7a64103e58b9"
  },
  {
    "url": "static/css/electrostatic.27bdc36e.chunk.css",
    "revision": "f146064502262bf03548b5284f852172"
  },
  {
    "url": "static/css/embed.2cea5d21.chunk.css",
    "revision": "2b31483ac6f20b032ee2a7a96acb3c52"
  },
  {
    "url": "static/css/energies.699bce96.chunk.css",
    "revision": "3fb7e1b351b85503abd6536a9f4553f3"
  },
  {
    "url": "static/css/epitopes.84641aa4.chunk.css",
    "revision": "806a54278b1fe51d33cbdbe9765146c3"
  },
  {
    "url": "static/css/files.7fc24f97.chunk.css",
    "revision": "6593360926599bac722b0d0b44a36b72"
  },
  {
    "url": "static/css/fluctuation.604fa437.chunk.css",
    "revision": "c288868c56842bdbe30740e336076b2b"
  },
  {
    "url": "static/css/footer.95a60a0a.chunk.css",
    "revision": "ddcac32b217b54438cfa30af2b3a0624"
  },
  {
    "url": "static/css/graph-msm.c53e0bfc.chunk.css",
    "revision": "a6b10e962832c2bd88675ba2c1a72413"
  },
  {
    "url": "static/css/graph.9dce14a8.chunk.css",
    "revision": "efa32fd695b8ecf43895b5ff7a5d708e"
  },
  {
    "url": "static/css/hbonds.9d049dbd.chunk.css",
    "revision": "bbeeb729449f61c638a794fd951ce554"
  },
  {
    "url": "static/css/help.26d8be25.chunk.css",
    "revision": "bd11b04c2f3d1fd3e122ceb014b0c55b"
  },
  {
    "url": "static/css/home.5e40fa3b.chunk.css",
    "revision": "66405903170a90de7802ea3a1ad9950b"
  },
  {
    "url": "static/css/markov.91368815.chunk.css",
    "revision": "200f30d786de740d1e4c4f2ffc672cbc"
  },
  {
    "url": "static/css/meta-analysis.be00ff25.chunk.css",
    "revision": "532685c3858759c8f3e285adda677291"
  },
  {
    "url": "static/css/mutations.76578838.chunk.css",
    "revision": "7ef78a481f750590932f0adda44e6282"
  },
  {
    "url": "static/css/overview.3a6f5cc4.chunk.css",
    "revision": "1da866e9d7f684de056d99d6b2f7ae64"
  },
  {
    "url": "static/css/pca.6ce67e89.chunk.css",
    "revision": "fe0646fba5b422f95e2ae9566017875b"
  },
  {
    "url": "static/css/pockets.f724903d.chunk.css",
    "revision": "1916162802bc70a4f3e20b0f68ab8e52"
  },
  {
    "url": "static/css/project-menu.c32676f9.chunk.css",
    "revision": "b26e1dbe808243f02166d0661fc6a5b1"
  },
  {
    "url": "static/css/projections.80968645.chunk.css",
    "revision": "b941cdd9c271dccb4b7ee7b1637f0ea1"
  },
  {
    "url": "static/css/rgyr.4793db4e.chunk.css",
    "revision": "4f84453d94cca83c0291ea6a2b935f2f"
  },
  {
    "url": "static/css/rmsd-pairwise.bd84f96b.chunk.css",
    "revision": "63408ff4f1e68b0cff6394364ec3816a"
  },
  {
    "url": "static/css/rmsd-perres.c2ae8cd3.chunk.css",
    "revision": "2f41f053983828716582aa91419fafe6"
  },
  {
    "url": "static/css/rmsds.4f403808.chunk.css",
    "revision": "533f5612f8457da935e378180fdd5a5d"
  },
  {
    "url": "static/css/sasa.88743c7e.chunk.css",
    "revision": "229561565afc6738607f719e97232c13"
  },
  {
    "url": "static/css/trajectory.0b9de092.chunk.css",
    "revision": "e7ef0cbc9643a0a4c23a3c52479e8ba6"
  },
  {
    "url": "static/css/viewer-with-controls.3dff3717.chunk.css",
    "revision": "48ab3c1bc67270d5726ee518d29e716d"
  },
  {
    "url": "static/js/1235.60486847.chunk.js",
    "revision": "9adf25b1ea1dafc7dac6474f77ca9a54"
  },
  {
    "url": "static/js/1280.8bab92ed.chunk.js",
    "revision": "afe856a4f2e0b63e4a1abd94888a18c6"
  },
  {
    "url": "static/js/1502.4a720608.chunk.js",
    "revision": "9a29410e4230900d653b53873e4cf83d"
  },
  {
    "url": "static/js/1772.47b57922.chunk.js",
    "revision": "00674776948e09eff6582986167a4323"
  },
  {
    "url": "static/js/1993.68bbdc5e.chunk.js",
    "revision": "9f8890f9a979685d0fd40f23d575333b"
  },
  {
    "url": "static/js/2260.40a49338.chunk.js",
    "revision": "cf5e8ab9915743671ed7196e395936a2"
  },
  {
    "url": "static/js/2577.fab5e066.chunk.js",
    "revision": "a87ebd5b564f87316bdc3f2cb1846a78"
  },
  {
    "url": "static/js/2594.0d5ff11a.chunk.js",
    "revision": "836499ae334ea3dfa6a1eaf18cb96b39"
  },
  {
    "url": "static/js/2597.d10a17a1.chunk.js",
    "revision": "7efc30d14ffbecece295c5f186c8ae4b"
  },
  {
    "url": "static/js/2599.fe30a534.chunk.js",
    "revision": "c8dddf15bf60a76c0f4369c9ba5bdd1d"
  },
  {
    "url": "static/js/3173.5b0cca08.chunk.js",
    "revision": "1ba0cde48ea451aab58bf0d562131085"
  },
  {
    "url": "static/js/3316.9f3c4c96.chunk.js",
    "revision": "8a9ff36cb10d6e636d40081eacbb2ee4"
  },
  {
    "url": "static/js/3506.eb06f0e8.chunk.js",
    "revision": "a7641f5708e542a11c6dd6c8e2081327"
  },
  {
    "url": "static/js/3784.c57bd069.chunk.js",
    "revision": "653bc8f965b8cf0a07dfae57e3189ceb"
  },
  {
    "url": "static/js/3809.5f683db1.chunk.js",
    "revision": "f5d18f2d408a48d00d24946f72844882"
  },
  {
    "url": "static/js/3845.2657bd9a.chunk.js",
    "revision": "4e52e98950a9efbebbce1f3bdbd6ae8c"
  },
  {
    "url": "static/js/4040.a73e0a60.chunk.js",
    "revision": "246a1efa02a4a5725a59201d6de9908a"
  },
  {
    "url": "static/js/4817.c6b1340d.chunk.js",
    "revision": "5f98b589df6a75ee77c611be92ed9f7c"
  },
  {
    "url": "static/js/5291.bb2520eb.chunk.js",
    "revision": "f182f9e364224b015b615b08d9dd3ef8"
  },
  {
    "url": "static/js/5577.09464e5c.chunk.js",
    "revision": "c9cb432116b50fa5a84254ceee66900e"
  },
  {
    "url": "static/js/5839.0b0e82e3.chunk.js",
    "revision": "95b91e886f81dcf3ee5992a927387cf4"
  },
  {
    "url": "static/js/6190.0e97a8a2.chunk.js",
    "revision": "75674c9c1828768d7cf9ad639db8664b"
  },
  {
    "url": "static/js/6264.763c2691.chunk.js",
    "revision": "5dad76a28ee33366b31053ded95b2816"
  },
  {
    "url": "static/js/7415.cac6d058.chunk.js",
    "revision": "d8ba0c654ca121ae1eaa75f721ad82d8"
  },
  {
    "url": "static/js/7784.639d4fb2.chunk.js",
    "revision": "fb5b3b45ce0b6cae2e21317178a181d5"
  },
  {
    "url": "static/js/7803.c947e297.chunk.js",
    "revision": "bcd968ad932e2b852d36a8ee5cd97489"
  },
  {
    "url": "static/js/7885.9c226137.chunk.js",
    "revision": "a19f4522b6b6f2bebc4d2bc36a456433"
  },
  {
    "url": "static/js/8095.c9954aed.chunk.js",
    "revision": "71077c4683af006ba88d92b8f916840f"
  },
  {
    "url": "static/js/8280.c3733cc9.chunk.js",
    "revision": "96ef5b4acfb20815341f327f2a0783c0"
  },
  {
    "url": "static/js/8324.c468749f.chunk.js",
    "revision": "51ace3c3c436884de21c3f4a2cad0dd8"
  },
  {
    "url": "static/js/9070.30a98a56.chunk.js",
    "revision": "c040f73171fecc2f3d9ad00f7e1e5242"
  },
  {
    "url": "static/js/9072.fab049b4.chunk.js",
    "revision": "ddd8f357e657c04d3d85ab6650b15f76"
  },
  {
    "url": "static/js/9256.9bd15834.chunk.js",
    "revision": "d26e897a22c18a141a7e2a29e3c89660"
  },
  {
    "url": "static/js/9349.aefaf0e5.chunk.js",
    "revision": "6bdddd194b52813d91a9ff58dd33882f"
  },
  {
    "url": "static/js/accession.8e7de467.chunk.js",
    "revision": "230a99b4189f83af97380cfb7b4a97fa"
  },
  {
    "url": "static/js/advanced-search.19d9b8a1.chunk.js",
    "revision": "3d0d91c67b39af93870c27f75b3f45c8"
  },
  {
    "url": "static/js/browse.d9ce79b3.chunk.js",
    "revision": "f974671faf751ccc7b616442ca62ee7b"
  },
  {
    "url": "static/js/contact.6720a3ef.chunk.js",
    "revision": "1137e54d6d8cdad0aa2e037c0c2898e1"
  },
  {
    "url": "static/js/custom-search.aa381015.chunk.js",
    "revision": "4c19a5489d421d02de8a118647d2d3ba"
  },
  {
    "url": "static/js/dist-perres.38d332d6.chunk.js",
    "revision": "2731f20e93935e7adf1f76f1b080b47a"
  },
  {
    "url": "static/js/electrostatic.eec0df5c.chunk.js",
    "revision": "9dbca8ee1a45dc093d486a8771c5c92c"
  },
  {
    "url": "static/js/embed.ad52e0b2.chunk.js",
    "revision": "17ea2d93d51a2bd9934bc547fcc997a7"
  },
  {
    "url": "static/js/energies.a6a641b2.chunk.js",
    "revision": "7fbd7f71a41740c446e0719c51ab5029"
  },
  {
    "url": "static/js/epitopes.8de87d7a.chunk.js",
    "revision": "da700d4400d4c54147468cc81a940ac1"
  },
  {
    "url": "static/js/files.94a8ffcb.chunk.js",
    "revision": "a2bbc5f056f06d8be75e7b4a51267cae"
  },
  {
    "url": "static/js/fluctuation.e42aab19.chunk.js",
    "revision": "08afdb4e1e613612240202001f3ea470"
  },
  {
    "url": "static/js/footer.73e83dd7.chunk.js",
    "revision": "d0a06563cb8a17addb49aaf8602a0159"
  },
  {
    "url": "static/js/graph-msm.614f3f6e.chunk.js",
    "revision": "35e91458839961f5790577d2293c8382"
  },
  {
    "url": "static/js/graph.70273ab9.chunk.js",
    "revision": "591c99564f2f6500c450f97fa5cae5ad"
  },
  {
    "url": "static/js/hbonds.1024e299.chunk.js",
    "revision": "1a6a5c3bb27a5f1e35e88c5418cdf959"
  },
  {
    "url": "static/js/help.87528a61.chunk.js",
    "revision": "af0fa26331ddafe5daf88abf7a76d534"
  },
  {
    "url": "static/js/home.4190512f.chunk.js",
    "revision": "29a832db01777489769ea02dddc45f94"
  },
  {
    "url": "static/js/intersection-observer.e95f0f77.chunk.js",
    "revision": "cc2fe391bcb1ed4e666b9b61e9ea42c6"
  },
  {
    "url": "static/js/json.bbb22e02.chunk.js",
    "revision": "31e2592213e24c5d52ed996a4a8dccec"
  },
  {
    "url": "static/js/main.c722b091.js",
    "revision": "8782c7842e77faee911a693338477943"
  },
  {
    "url": "static/js/markov.8816f785.chunk.js",
    "revision": "992796276a879a88ba4e8f77980bbd37"
  },
  {
    "url": "static/js/meta-analysis.3ec09dd6.chunk.js",
    "revision": "900880fb172d04c957c9bff7976b80d1"
  },
  {
    "url": "static/js/mutations.90210906.chunk.js",
    "revision": "4d3a992317afc0e6000d228947afcd2a"
  },
  {
    "url": "static/js/overview.9d162427.chunk.js",
    "revision": "8d30519aba9b700811f381db6c2f6897"
  },
  {
    "url": "static/js/pca.976b8654.chunk.js",
    "revision": "cc9c9e794acad6592929c79a4c87c9ae"
  },
  {
    "url": "static/js/pockets.0a15a62e.chunk.js",
    "revision": "fad89976185318dc0a9f1c4dbc8a69fc"
  },
  {
    "url": "static/js/project-menu.43f2dff3.chunk.js",
    "revision": "90547e4146f5fe1f0c557999b995e9a3"
  },
  {
    "url": "static/js/projections.e2da77d4.chunk.js",
    "revision": "a74bfe685d2ebc0f3c8f0ce0c8915e5d"
  },
  {
    "url": "static/js/protvista-coloured-sequence.444c6cb1.chunk.js",
    "revision": "da9e1811b0b1cf59e80270da09728ffb"
  },
  {
    "url": "static/js/protvista-interpro-track.c43cde23.chunk.js",
    "revision": "f27542cdc7c82ff82c849a3f8a74e907"
  },
  {
    "url": "static/js/protvista-manager.d7b8799f.chunk.js",
    "revision": "2602e97534f517b1b638b0e40c77c4e7"
  },
  {
    "url": "static/js/protvista-navigation.f7ef863f.chunk.js",
    "revision": "5ebb01621276ab27ac30e2e07d0e8cf2"
  },
  {
    "url": "static/js/protvista-sequence.b7fa3cdd.chunk.js",
    "revision": "1989e16d756966257fdcd50e0cf7c19b"
  },
  {
    "url": "static/js/rgyr.819cad5d.chunk.js",
    "revision": "ec53c9476298ae6859dda919f1117b0d"
  },
  {
    "url": "static/js/rmsd-pairwise.cbe607a7.chunk.js",
    "revision": "e28dfc900be24e3a161174eb90241bb8"
  },
  {
    "url": "static/js/rmsd-perres.d73bbd82.chunk.js",
    "revision": "e7a5686abc65038383f6536c1a33b586"
  },
  {
    "url": "static/js/rmsds.a4fb583f.chunk.js",
    "revision": "ff27af41dab1ac7a55ccb665d3e76c67"
  },
  {
    "url": "static/js/sasa.ac4541be.chunk.js",
    "revision": "7f97f6b379af3786c2b5a669aafdb46d"
  },
  {
    "url": "static/js/snack-bar-container.ec05da94.chunk.js",
    "revision": "e88ddf43e202c09948c289348ffe2846"
  },
  {
    "url": "static/js/trajectory.686fa404.chunk.js",
    "revision": "7ed82f6a67b0d9c60d1f7e6b4ee2003c"
  }
], {}); // content will be injected here

// navigation route (any navigation request to any part of the scope of the service worker)
workbox.routing.registerNavigationRoute(
  workbox.precaching.getCacheKeyForURL('./index.html'),
  {
    blacklist: [
      /^\/_/,
      /\/[^\/]+\.[^\/]+$/,
      /\/api\//, // avoid responding to /api, because it should be outside of the scope of that service worker
      /\/optimade\//, // avoid responding to /optimade, because it should be outside of the scope of that service worker
    ],
  },
);

// routing recipes
// see: https://developers.google.com/web/tools/workbox/guides/common-recipes
// images - Cache First
workbox.routing.registerRoute(
  /\.(?:png|gif|jpg|jpeg|webp|svg|ico)$/,
  new workbox.strategies.CacheFirst({
    cacheName: 'images',
    plugins: [
      new workbox.expiration.Plugin({
        maxEntries: 100,
        maxAgeSeconds: 40 * DAY,
      }),
    ],
  }),
);

// external images - Cache First
workbox.routing.registerRoute(
  /^https?:\/\/.*?\.(?:png|gif|jpg|jpeg|webp|svg)$/,
  new workbox.strategies.CacheFirst({
    cacheName: 'external-images',
    plugins: [
      new workbox.cacheableResponse.Plugin({ statuses: [0, 200] }),
      new workbox.expiration.Plugin({
        maxEntries: 10,
        maxAgeSeconds: 20 * DAY,
        purgeOnQuotaError: true,
      }),
    ],
  }),
);

// static assets - Cache First
// (usually, just fonts then, since images are handled before)
workbox.routing.registerRoute(
  /\/static\//,
  new workbox.strategies.CacheFirst({
    cacheName: 'static',
    plugins: [
      new workbox.expiration.Plugin({
        maxEntries: 30,
        maxAgeSeconds: 10 * WEEK,
        // it's alright if it's purged, we're using display-font: swap anyway
        purgeOnQuotaError: true,
      }),
    ],
  }),
);

// api calls - Stale While Revalidate
// (except for trajectory files, because of ranged requests)
workbox.routing.registerRoute(
  // the missing "t" below is on purpose!!! Do not think you need to fix it!
  // It's to get basically, anything not finishing by "ajectory", or
  // "ajectory.bin", or "ajectory.trj", or "ajectory.traj"
  /^https?:\/\/mmb.irbbarcelona.org\/.*\/api\/rest\/(.(?!rajectory(\.(tra?j|bin))?$))+$/,
  new workbox.strategies.StaleWhileRevalidate({
    cacheName: 'api-calls',
    plugins: [
      new workbox.expiration.Plugin({
        maxEntries: 100,
        maxAgeSeconds: 40 * DAY,
        purgeOnQuotaError: true,
      }),
    ],
  }),
);
