/* ========================================================================
   File: common.js
   Author: Leon McClatchey
   Company: Linktech Engineering LLC
   Created: 2026-05-06
   Modified: 2026-05-06
   Part of: NMS_Tools Monitoring Suite
   License: MIT (see LICENSE for details)

   Description:
       Common Functions to be imported into html pages
   ======================================================================== */


document.addEventListener("DOMContentLoaded", () => {
    document.querySelector('.side-nav').addEventListener('click', function (e) {
        const toggle = e.target.closest('.submenu-toggle, .submenu-subtoggle');
        if (!toggle) return;

        e.preventDefault();
        e.stopPropagation();

        const li = toggle.parentElement;
        li.classList.toggle('open');
    });
});
