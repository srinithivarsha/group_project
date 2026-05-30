// Update notification count on page load and periodically
$(document).ready(function() {
    // Function to update notification count
    function updateNotificationCount() {
        $.ajax({
            url: '/notifications/count',
            method: 'GET',
            success: function(response) {
                const badge = $('#notificationBadge');
                if (response.count > 0) {
                    badge.text(response.count).show();
                } else {
                    badge.hide();
                }
            }
        });
    }
    
    // Update count on page load
    updateNotificationCount();
    
    // Update every 30 seconds
    setInterval(updateNotificationCount, 30000);
    // Update notification count on page load and periodically
$(document).ready(function() {
    // Function to update notification count
    function updateNotificationCount() {
        $.ajax({
            url: '/notifications/count',
            method: 'GET',
            success: function(response) {
                const badge = $('#notificationBadge');
                if (response.count > 0) {
                    badge.text(response.count).show();
                } else {
                    badge.hide();
                }
            }
        });
    }
    
    // Update count on page load
    updateNotificationCount();
    
    // Update every 30 seconds
    setInterval(updateNotificationCount, 30000);
});
});