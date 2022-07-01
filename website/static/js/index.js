function updateVisibleAffiliates() {
    let filters = document.querySelectorAll("#filters input");
    let shownFilters = [];
    for(let f of filters) {
        if(f.checked) shownFilters.push(f.dataset.filter);
    }
    for(let aff of document.querySelectorAll(".affiliate")) {
        let show = false;
        for(let tag of aff.dataset.tags.split(',')) {
            show = show || shownFilters.includes(tag);
        }
        if(show) {
            aff.style.display = "flex";
        }
        else {
            aff.style.display = "none";
        }
    }
}
