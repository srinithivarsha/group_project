
const RationSystem = {
    
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    },
    
   
    formatCurrency: function(amount) {
        return '₹' + parseFloat(amount).toFixed(2);
    },
    
    showNotification: function(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        
        $('.container').prepend(alertHtml);
        
        setTimeout(() => {
            $('.alert').first().alert('close');
        }, 5000);
    },
    
   
    validateCardNumber: function(cardNumber) {
        const pattern = /^[A-Z]{2}[0-9]{10}$/;
        return pattern.test(cardNumber);
    },
    

    calculateRemainingQuota: function(purchases, quota) {
        const remaining = {
            rice: quota.rice_quota,
            wheat: quota.wheat_quota,
            sugar: quota.sugar_quota,
            kerosene: quota.kerosene_quota
        };
        
        purchases.forEach(purchase => {
            const item = purchase.item_name.toLowerCase();
            if (remaining.hasOwnProperty(item)) {
                remaining[item] -= purchase.quantity;
            }
        });
        
        return remaining;
    },
    
   
    getStockStatus: function(quantity) {
        if (quantity > 100) return { text: 'In Stock', class: 'success' };
        if (quantity > 0) return { text: 'Low Stock', class: 'warning' };
        return { text: 'Out of Stock', class: 'danger' };
    }
};

$(document).ready(function() {
    console.log('Ration Card System initialized');
    
    
    const currentPath = window.location.pathname;
    $('.nav-link').each(function() {
        const linkPath = $(this).attr('href');
        if (currentPath === linkPath || 
           (currentPath.includes(linkPath) && linkPath !== '/')) {
            $(this).addClass('active');
        }
    });
    
    
    setTimeout(() => {
        $('.alert').alert('close');
    }, 5000);
    
   
    $('form').on('submit', function(e) {
        const requiredFields = $(this).find('[required]');
        let isValid = true;
        
        requiredFields.each(function() {
            if (!$(this).val().trim()) {
                isValid = false;
                $(this).addClass('is-invalid');
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            RationSystem.showNotification('Please fill all required fields', 'warning');
        }
    });
    
   
    $('input, select, textarea').on('input', function() {
        $(this).removeClass('is-invalid');
    });
});