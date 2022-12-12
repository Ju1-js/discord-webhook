function activeTab() {
  var child = get_uiCurrentTab();
  return Array.prototype.indexOf.call(child.parentNode.children, child);
}

function getImages(_, txt2img, img2img) {
  if (activeTab() == 0) {
    return extract_image_from_gallery(txt2img);
  } else if (activeTab() == 1) {
    return extract_image_from_gallery(img2img);
  }
}
