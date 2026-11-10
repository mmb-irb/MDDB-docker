# Client

The **website client** is the [MDposit client](https://github.com/mmb-irb/MDposit-client), a **React** app built with **Vite**.

## Dockerfile

The [Dockerfile](Dockerfile) builds the client from its source code and serves the build with **nginx**:

1. It clones the client repository at the version given in the `VERSION` build argument (e.g. `0.0.22` for the tag `v0.0.22`).
   Without `VERSION` it uses the latest release, or the latest version tag if the repository has no releases.
2. If there is a [node host configuration file](#host-configuration-file) it copies it into the client source code.
3. It builds the client (`npm ci` and `npm run build`) and copies the build into an **nginx** image, which exposes the port `CLIENT_INNER_PORT`.

The client version is written in `/app/version.txt` inside the image, as for the other services.

Build a concrete version with:

```bash
python3 scripts/rebuild-legacy.py -s client -v 0.0.22 -t my_stack
```

## Host configuration file

The client behaviour (target API, name, logos, colors, contact, search fields...) is set in its host configuration.
Without a node configuration the client uses its [default host configuration](https://github.com/mmb-irb/MDposit-client/blob/master/src/utils/constants/default-host-config.js), which is a generic MDposit look with the API in the same domain as the page.
So every node which wants its own name, colors, footers or contacts needs its own configuration file.

To give this node its own configuration, create the file **`client/host-config.js`**.
It is ignored by git, so every node keeps its own one.
The build copies it as `host-config.js` at the root of the client repository, where the client looks for it.
This needs the client **v0.0.22 or newer**: with an older version the build stops with an error.

Start from one of the examples in the client repository, which have a short description of every field:

* [example-single-host-config.js](https://github.com/mmb-irb/MDposit-client/blob/master/example-single-host-config.js): one single configuration, for a node with one URL or which looks the same in all of them.
* [example-multiple-host-config.js](https://github.com/mmb-irb/MDposit-client/blob/master/example-multiple-host-config.js): a different configuration for each URL (domain) which serves the client, e.g. a production and a development domain.

Take the examples from the client version you deploy (change `master` in the link by the tag, e.g. `v0.0.22`).

About this file:

* It only needs the fields which are different for this node: the client fills the missing ones with its default values.
* It is JavaScript with JSX, and it can import anything from the client source code with `src/...` (images, query fields, auxiliar functions).
* Images of this node (e.g. footer logos) go in the folder **`client/images/`**, also ignored by git.
  The build copies them to `src/images/untracked/` in the client, so `host-config.js` imports them as `src/images/untracked/<file>`.
  The client examples import `src/images/untracked/my-lab-logo.png`: put that image in `client/images/` or remove the import.

The configuration is part of the build, so **rebuild the client after changing it**:

```bash
python3 scripts/rebuild.py -s client -t my_stack
```

In development mode ([Dockerfile.dev](Dockerfile.dev)) the client is built from `client/MDposit-client`, and `client/host-config.js` and `client/images/` are used the same way.
