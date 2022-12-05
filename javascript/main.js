function activeTab() {
  var child = gradioApp()
    .querySelector("#tabs")
    .querySelector("button.bg-white");
  var index = Array.prototype.indexOf.call(child.parentNode.children, child);
  return index;
}

function selected_gallery_index() {
  var buttons = gradioApp().querySelectorAll(
    '[style="display: block;"].tabitem div[id$=_gallery] .gallery-item'
  );
  var button = gradioApp().querySelector(
    '[style="display: block;"].tabitem div[id$=_gallery] .gallery-item.\\!ring-2'
  );

  var result = -1;
  buttons.forEach(function (v, i) {
    if (v == button) {
      result = i;
    }
  });

  return result;
}

function extract_image_from_gallery(gallery) {
  if (gallery.length == 1) {
    return gallery[0];
  }

  index = selected_gallery_index();

  if (index < 0 || index >= gallery.length) {
    return [null];
  }

  return gallery[index];
}

function get_tab_index(tabId) {
  var res = 0;

  gradioApp()
    .getElementById(tabId)
    .querySelector("div")
    .querySelectorAll("button")
    .forEach(function (button, i) {
      if (button.className.indexOf("bg-white") != -1) res = i;
    });

  return res;
}
