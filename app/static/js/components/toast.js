/**
 * Toast notification component.
 */

export class Toast {
    static show(message, type = 'info', duration = 3500) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                z-index: 9999;
            `;
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        const borderColor = type === 'success' ? 'var(--color-profit-text)' :
                            type === 'error' ? 'var(--color-loss-text)' : 'var(--color-accent)';

        toast.style.cssText = `
            background-color: var(--bg-surface);
            color: var(--text-main);
            border-left: 3px solid ${borderColor};
            border: 1px solid var(--border-medium);
            padding: 10px 14px;
            border-radius: var(--radius-sm);
            font-size: 12px;
            font-family: var(--font-sans);
            box-shadow: 0 4px 16px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 240px;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.2s ease;
        `;

        toast.innerHTML = `<span>${message}</span>`;
        container.appendChild(toast);

        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 250);
        }, duration);
    }
}
